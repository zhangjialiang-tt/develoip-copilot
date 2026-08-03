"""OMP <-> Python Runtime bridge (stdio, newline-delimited JSON).

Start with::

    python -m runtime.omp_bridge --stdio [--state-dir .omp/dc-state]

The bridge only translates protocol frames. All state authority stays in
``Runtime.dispatch()``; the bridge never mutates objects, never writes
Derived Results, and never imports OMP session history as fact.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from .candidates import build_candidate_commands
from .core import Runtime
from .errors import ContractError
from .omp_protocol import PROTOCOL_VERSION, ProtocolError, error_frame, parse_request, response_frame
from .persistence import JsonlEventStore
from .roles import REQUIRED_REQUEST_FIELDS, ROLE_RESPONSE_FIELDS, RoleInvocationLayer
from .schema import SCHEMA_VERSION

DC_ROLES = (
    "orchestrator",
    "system-investigator",
    "rtl-engineer",
    "verification-engineer",
    "integration-reviewer",
    "documenter",
)
ROLE_ALIASES = {f"dc-{role}": role for role in DC_ROLES}
TERMINAL_TASK_STATUSES = {"CLOSED", "CANCELLED"}
FORBIDDEN_ROLE_FIELDS = {"gate_status", "claim_status", "closure_status", "project_status", "approval_granted", "task_closed"}

# Conservative write-intent heuristics for bash interception (M3-O04).
BASH_WRITE_PATTERNS = (
    re.compile(r"\bsed\s+(-i\b|--in-place)"),
    re.compile(r"\b(rm|rmdir|del|erase|mv|move|cp|copy|ren|rename|chmod|chown|attrib|tee|truncate|dd)\b"),
    re.compile(r"(^|[;&|])\s*[^<>&|]*>>?\s*[^&|]"),
    re.compile(r"\bgit\s+(checkout\s+--|restore|reset|clean|push|commit|merge|rebase|switch|checkout\s+\S)"),
    re.compile(r"\b(mkdir|md)\b"),
    re.compile(r"\b(Set-Content|Out-File|Add-Content|Clear-Content|New-Item|Remove-Item|Move-Item|Copy-Item)\b", re.IGNORECASE),
    re.compile(r"\bpython\S*\s+.*\b-c\b.*\b(open|write|unlink|rmtree)\b"),
)

NEXT_ACTIONS_BY_STATUS = {
    "PROPOSED": ["CLASSIFY_TASK", "CANCEL_TASK"],
    "READY": ["START_TASK", "CHANGE_BASELINE"],
    "AWAITING_APPROVAL": ["REQUEST_APPROVAL", "GRANT_APPROVAL (user)", "REJECT_APPROVAL (user)"],
    "RUNNING": ["invoke roles via dc_invoke_role", "REGISTER_EVIDENCE", "FINISH_TASK"],
    "AWAITING_VALIDATION": ["REGISTER_EVIDENCE", "RECORD_ACCEPTANCE"],
    "REWORK_REQUIRED": ["START_TASK (rework)", "CANCEL_TASK"],
}


def normalize_path(value: str) -> str:
    return str(value).replace("\\", "/").strip().rstrip("/")


def classify_bash(command: str) -> tuple[str, str]:
    """Return (READ|WRITE_LIKELY, matched pattern source)."""
    for pattern in BASH_WRITE_PATTERNS:
        if pattern.search(command):
            return "WRITE_LIKELY", pattern.pattern
    return "READ", ""


def _bash_write_targets(command: str) -> list[str]:
    """Extract candidate write-target tokens from a bash command.

    Heuristic, documented in milestone3-omp-decisions.md. Used by the guard to
    decide whether a command writes INTO a governed scope (target-aware), as
    opposed to merely mentioning a governed path (e.g. as a copy source).
    """
    targets: list[str] = []
    # redirections: > file, >> file, 1> file, 2> file, &> file (with or without space)
    for match in re.finditer(r"(?:^|[;&|]|\s)(?:[12]?>>?|&>)\s*([^\s;&|]+)", command):
        targets.append(match.group(1))
    # -o / -of target
    for match in re.finditer(r"(?:^|\s)(?:-o|-of)\s+([^\s]+)", command):
        targets.append(match.group(1))
    # dd of=target
    for match in re.finditer(r"\bof=([^\s]+)", command):
        targets.append(match.group(1))
    # cp/mv/install destination = last positional token
    match = re.search(r"\b(?:cp|mv|install)\s+.*?\s([^\s]+)\s*$", command)
    if match:
        targets.append(match.group(1))
    # sed -i <expr> <file>: last positional token
    if re.search(r"\bsed\s+(-i\b|--in-place)", command):
        match = re.search(r"\bsed\s+(-i\b|--in-place)\s+.*?\s([^\s]+)\s*$", command)
        if match:
            targets.append(match.group(2))
    # git working-tree mutations with paths: checkout -- / restore / reset / clean
    match = re.search(r"\bgit\s+(?:checkout(?:\s+--)?|restore|reset|clean)\s+(.*)$", command)
    if match:
        targets.extend(token for token in re.split(r"\s+", match.group(1)) if token and not token.startswith("-"))
    return targets


class BridgeServer:
    """Handles bridge ops against one Runtime instance."""

    def __init__(self, runtime: Runtime, state_dir: Path, config: dict[str, Any]):
        self.runtime = runtime
        self.state_dir = state_dir
        self.config = config
        self.started_at = time.time()
        self.role_layer = RoleInvocationLayer()
        for role in DC_ROLES:
            self.role_layer.register(role, lambda request: request.get("_candidate", {}))

    # -- frame routing -------------------------------------------------
    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        op = request["op"]
        params = request["params"]
        if op == "shutdown":
            return None
        handler = getattr(self, f"_op_{op}")
        result = handler(params)
        return result

    # -- ops -----------------------------------------------------------
    def _op_hello(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocol_version": PROTOCOL_VERSION,
            "schema_version": SCHEMA_VERSION,
            "service": "develoip-copilot-bridge",
            "ops": ["hello", "health", "status", "dispatch", "query", "restore", "save_snapshot", "invoke_role_result", "submit_candidates", "guard_check", "workspace_status", "capture_baseline", "shutdown"],
            "role_request_fields": list(REQUIRED_REQUEST_FIELDS),
            "role_response_fields": sorted(ROLE_RESPONSE_FIELDS),
            "forbidden_role_fields": sorted(FORBIDDEN_ROLE_FIELDS),
            "roles": list(DC_ROLES),
            "event_store": str(self.runtime.event_store.path) if self.runtime.event_store.path else None,
            "last_sequence": self.runtime.event_store.last_sequence(),
            "state_dir": str(self.state_dir),
        }

    def _op_health(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "pid": __import__("os").getpid(),
            "uptime_seconds": round(time.time() - self.started_at, 3),
            "last_sequence": self.runtime.event_store.last_sequence(),
        }

    def _op_status(self, _params: dict[str, Any]) -> dict[str, Any]:
        tasks = [self.runtime.query(task_id) for task_id in self.runtime.state["Task"]]
        pending_approvals = [a for a in self.runtime.state["Approval"].values() if a.get("status") == "REQUESTED"]
        active_blockers = [b for b in self.runtime.state["Blocker"].values() if not b.get("resolved")]
        return {
            "last_sequence": self.runtime.event_store.last_sequence(),
            "tasks": tasks,
            "pending_approvals": pending_approvals,
            "active_blockers": active_blockers,
            "next_legal_actions": {
                task["object_id"]: NEXT_ACTIONS_BY_STATUS.get(task.get("execution_status"), [])
                for task in tasks
                if task.get("execution_status") not in TERMINAL_TASK_STATUSES
            },
        }

    def _op_dispatch(self, params: dict[str, Any]) -> dict[str, Any]:
        command = params.get("command")
        if not isinstance(command, dict):
            raise ContractError("COMMAND_INVALID", "dispatch params need a command object")
        return self.runtime.dispatch(command)

    def _op_query(self, params: dict[str, Any]) -> dict[str, Any]:
        object_id = params.get("object_id")
        if not isinstance(object_id, str) or not object_id:
            raise ContractError("BRIDGE_PARAMS_INVALID", "query needs object_id")
        return {"object": self.runtime.query(object_id, params.get("object_type"))}

    def _op_restore(self, params: dict[str, Any]) -> dict[str, Any]:
        snapshot = params.get("snapshot_path") or self._snapshot_path()
        self.runtime = Runtime.restore(self.runtime.event_store, snapshot)
        return {"restored": True, "last_sequence": self.runtime.event_store.last_sequence()}

    def _op_save_snapshot(self, params: dict[str, Any]) -> dict[str, Any]:
        path = self.runtime.save_snapshot(params.get("path") or self._snapshot_path())
        return {"snapshot_path": str(path), "last_sequence": self.runtime.event_store.last_sequence()}

    def _op_invoke_role_result(self, params: dict[str, Any]) -> dict[str, Any]:
        request = dict(params.get("request") or {})
        output = params.get("output")
        if not isinstance(output, dict):
            raise ContractError("ROLE_RESPONSE_INVALID", "Role output must be an object")
        request["role"] = ROLE_ALIASES.get(request.get("role", ""), request.get("role"))
        request["_candidate"] = output
        validated = self.role_layer.invoke(request)
        request.pop("_candidate", None)
        return {"validated": validated, "request": request}

    def _op_submit_candidates(self, params: dict[str, Any]) -> dict[str, Any]:
        validated = self._op_invoke_role_result(params)["validated"]
        task = self.runtime.query(params.get("request", {}).get("task_ref", ""), "Task")
        actor = params.get("actor") or validated["role"]
        try:
            candidates = build_candidate_commands(validated, task, actor)
        except ValueError as error:
            raise ContractError("CANDIDATE_INVALID", str(error)) from error
        return {"validated": validated, "candidate_commands": candidates, "note": "Candidates are proposals; dispatch each via dc_dispatch."}

    def _op_guard_check(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("tool_name")
        if tool_name not in {"edit", "write", "ast_edit", "bash"}:
            return {"allowed": True, "reason": "TOOL_NOT_GUARDED"}
        active_tasks = [
            self.runtime.query(task_id)
            for task_id, task in self.runtime.state["Task"].items()
            if task.get("execution_status") not in TERMINAL_TASK_STATUSES
        ]
        protected = [normalize_path(p) for p in self.config.get("protected_paths", [])]
        targets = [normalize_path(p) for p in params.get("paths", []) if isinstance(p, str) and p.strip()]
        for path in targets:
            if any(path == root or path.startswith(root + "/") for root in protected if root):
                return {"allowed": False, "code": "PROTECTED_PATH", "reason": f"Write target is protected: {path}"}
        workspace_block = self._workspace_conflict_block(targets)
        if workspace_block:
            return workspace_block
        if not active_tasks:
            return {"allowed": True, "reason": "NO_ACTIVE_TASK"}
        if tool_name == "bash":
            classification, matched = classify_bash(params.get("command") or "")
            if classification == "READ":
                return {"allowed": True, "reason": "BASH_READ_ONLY"}
            cwd = normalize_path(params.get("cwd") or "")
            governed = [task for task in active_tasks if self._bash_governed(cwd, params.get("command") or "", task)]
            if not governed:
                return {"allowed": True, "reason": "BASH_OUTSIDE_GOVERNED_SCOPE", "classification": classification, "matched": matched}
            return self._approval_decision(governed, classification=classification, matched=matched)
        governed = [task for task in active_tasks if any(self._path_in_task_scope(path, task) for path in targets)]
        if not governed:
            return {"allowed": True, "reason": "OUTSIDE_GOVERNED_SCOPE"}
        return self._approval_decision(governed)

    def _op_workspace_status(self, _params: dict[str, Any]) -> dict[str, Any]:
        pilot = self.config.get("pilot_repository")
        if not pilot:
            return {
                "pilot_repository": None,
                "pilot_connected": False,
                "note": "pilot_repository not configured; set .omp/dc-state/config.json",
                "event_store": str(self.runtime.event_store.path) if self.runtime.event_store.path else None,
                "last_sequence": self.runtime.event_store.last_sequence(),
                "workspace_classification": "UNKNOWN",
            }
        try:
            from workspace.adapter import WorkspaceAdapter

            adapter = WorkspaceAdapter(pilot)
            snapshot = adapter.snapshot(
                read_scope=self.config.get("read_scope"),
                write_scope=self.config.get("candidate_write_scope"),
                relevant_paths=self.config.get("relevant_paths", []),
                tool_versions=self.config.get("tool_versions", {}),
                input_data_refs=self.config.get("input_data_refs", []),
            )
            classification = adapter.classify(snapshot)
            return {
                "pilot_repository": pilot,
                "pilot_connected": True,
                "workspace_classification": classification,
                "branch": snapshot.get("branch"),
                "commit": snapshot.get("commit"),
                "tracked_modified": snapshot.get("tracked_modified"),
                "untracked": snapshot.get("untracked"),
                "relevant_file_hashes": snapshot.get("relevant_file_hashes"),
                "event_store": str(self.runtime.event_store.path) if self.runtime.event_store.path else None,
                "last_sequence": self.runtime.event_store.last_sequence(),
            }
        except Exception as error:  # noqa: BLE001 - adapter must never crash the bridge
            return {
                "pilot_repository": pilot,
                "pilot_connected": False,
                "workspace_classification": "UNKNOWN",
                "error": str(error),
                "event_store": str(self.runtime.event_store.path) if self.runtime.event_store.path else None,
                "last_sequence": self.runtime.event_store.last_sequence(),
            }

    def _op_capture_baseline(self, params: dict[str, Any]) -> dict[str, Any]:
        """Capture a real workspace Baseline (read-only) from the pilot repo."""
        pilot = params.get("pilot_repository") or self.config.get("pilot_repository")
        if not pilot:
            raise ContractError("PILOT_NOT_CONFIGURED", "pilot_repository is not configured")
        from workspace.adapter import WorkspaceAdapter
        from workspace.baseline import WorkspaceBaseline

        adapter = WorkspaceAdapter(pilot)
        relevant = params.get("relevant_paths") or self.config.get("relevant_paths", [])
        read_scope = params.get("read_scope") or self.config.get("read_scope")
        write_scope = params.get("write_scope") or self.config.get("candidate_write_scope")
        snapshot = adapter.snapshot(
            read_scope=read_scope,
            write_scope=write_scope,
            relevant_paths=relevant,
            tool_versions=params.get("tool_versions") or self.config.get("tool_versions", {}),
            input_data_refs=params.get("input_data_refs") or self.config.get("input_data_refs", []),
        )
        classification = adapter.classify(snapshot)
        baseline = WorkspaceBaseline(adapter).capture(snapshot)
        return {"baseline": baseline, "classification": classification, "snapshot": snapshot}

    # -- guard helpers ---------------------------------------------------
    def _workspace_conflict_block(self, targets: list[str]) -> dict[str, Any] | None:
        """Deny writes into a pilot workspace classified UNKNOWN/CONFLICTING (plan §13.4)."""
        pilot = self.config.get("pilot_repository")
        if not pilot or not targets:
            return None
        try:
            from workspace.adapter import WRITE_FORBIDDEN, WorkspaceAdapter

            adapter = WorkspaceAdapter(pilot)
            snapshot = adapter.snapshot(
                read_scope=self.config.get("read_scope"),
                write_scope=self.config.get("candidate_write_scope"),
                relevant_paths=self.config.get("relevant_paths", []),
            )
            classification = adapter.classify(snapshot)
        except Exception:  # noqa: BLE001 - adapter failure degrades to allow (active-task approval still gates)
            return None
        if classification not in WRITE_FORBIDDEN:
            return None
        return {
            "allowed": False,
            "code": "WORKSPACE_" + classification,
            "reason": f"Pilot workspace is {classification}; WRITE forbidden (plan §13.4). Resolve workspace state first.",
            "workspace_classification": classification,
        }

    def _approval_decision(self, tasks: list[dict[str, Any]], *, classification: str = "", matched: str = "") -> dict[str, Any]:
        details: list[dict[str, Any]] = []
        for task in tasks:
            blockers = [b for b in self.runtime.state["Blocker"].values() if b.get("task_ref") == task["object_id"] and not b.get("resolved")]
            if blockers:
                return {"allowed": False, "code": "BLOCKER_ACTIVE", "reason": f"Active Blocker on {task['object_id']}", "task": task["object_id"]}
            baseline_ref = task.get("baseline_ref")
            if not baseline_ref:
                details.append({"task": task["object_id"], "code": "BASELINE_REQUIRED"})
                continue
            granted = [
                approval for approval in self.runtime.state["Approval"].values()
                if approval.get("task_ref") == task["object_id"]
                and approval.get("status") == "GRANTED"
                and approval.get("baseline_ref") == baseline_ref
                and approval.get("requested_capability") == "WRITE"
            ]
            if granted:
                return {"allowed": True, "reason": "WRITE_APPROVAL_VALID", "task": task["object_id"], "approval": granted[0]["object_id"],
                        **({"classification": classification, "matched": matched} if classification else {})}
            pending = [
                approval for approval in self.runtime.state["Approval"].values()
                if approval.get("task_ref") == task["object_id"] and approval.get("status") == "REQUESTED"
            ]
            details.append({"task": task["object_id"], "code": "APPROVAL_PENDING" if pending else "APPROVAL_REQUIRED"})
        return {"allowed": False, "code": details[0]["code"] if details else "APPROVAL_REQUIRED",
                "reason": "No valid WRITE Approval covers the governed scope", "checks": details,
                **({"classification": classification, "matched": matched} if classification else {})}

    @staticmethod
    def _path_in_task_scope(path: str, task: dict[str, Any]) -> bool:
        for scope_path in task.get("scope", {}).get("paths", []):
            root = normalize_path(scope_path)
            if root and (path == root or path.startswith(root + "/")):
                return True
        return False

    def _bash_governed(self, cwd: str, command: str, task: dict[str, Any]) -> bool:
        """Target-aware bash governance: governed when the cwd OR an actual
        write target (redirection, -o, dd of=, cp/mv destination, sed -i file,
        git mutation path) lies inside the task scope. A governed path that
        only appears as a SOURCE (e.g. cp from the pilot to %TEMP%) does not
        count as a write into the scope."""
        scope_paths = [normalize_path(p) for p in task.get("scope", {}).get("paths", []) if normalize_path(p)]
        if not scope_paths:
            return False

        def in_scope(value: str) -> bool:
            normalized = normalize_path(value)
            return bool(normalized) and any(normalized == root or normalized.startswith(root + "/") for root in scope_paths)

        if cwd and in_scope(cwd):
            return True
        return any(in_scope(target) for target in _bash_write_targets(command))

    def _snapshot_path(self) -> Path:
        return self.state_dir / "snapshot.json"


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ContractError("BRIDGE_CONFIG_INVALID", f"Config is not valid JSON: {error}") from error
    if not isinstance(config, dict):
        raise ContractError("BRIDGE_CONFIG_INVALID", "Config must be a JSON object")
    return config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="runtime.omp_bridge")
    parser.add_argument("--stdio", action="store_true", required=True, help="serve over stdin/stdout JSONL")
    parser.add_argument("--state-dir", default=".omp/dc-state", help="event store / snapshot / config directory")
    args = parser.parse_args(argv)

    # The JSONL protocol is UTF-8. On Windows the locale code page (e.g. GBK)
    # otherwise mangles non-ASCII bytes into surrogate escapes. Force UTF-8 on
    # all three stdio streams regardless of environment.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass  # reconfigure unavailable or already binary

    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    config = _load_config(state_dir / "config.json")
    store = JsonlEventStore(state_dir / "events.jsonl")
    runtime = Runtime(store)
    server = BridgeServer(runtime, state_dir, config)
    print(f"dc-bridge ready state_dir={state_dir} last_sequence={store.last_sequence()}", file=sys.stderr, flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        request_id = None
        try:
            request = parse_request(line)
            request_id = request["id"]
            result = server.handle(request)
            if result is None:  # shutdown
                sys.stdout.write(response_frame(request_id, {"shutdown": True}) + "\n")
                sys.stdout.flush()
                return 0
            sys.stdout.write(response_frame(request_id, result) + "\n")
        except ProtocolError as error:
            sys.stdout.write(error_frame(request_id, error.code, error.message) + "\n")
        except ContractError as error:
            sys.stdout.write(error_frame(request_id, error.code, error.message, error.details) + "\n")
        except Exception as error:  # noqa: BLE001 - bridge must never crash on one frame
            sys.stdout.write(error_frame(request_id, "BRIDGE_INTERNAL_ERROR", str(error)) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
