from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .errors import ContractError
from .persistence import JsonlEventStore
from .schema import SCHEMA_VERSION, validate_object


ROLE_RULES = {
    "CREATE_TASK": {"orchestrator"},
    "CLASSIFY_TASK": {"orchestrator"},
    "PROPOSE_RISK": {"system-investigator", "rtl-engineer", "verification-engineer"},
    "ACTIVATE_RISK": {"orchestrator"},
    "BIND_BASELINE": {"orchestrator"},
    "CHANGE_BASELINE": {"orchestrator"},
    "START_TASK": {"orchestrator"},
    "REQUEST_APPROVAL": {"orchestrator", "rtl-engineer", "verification-engineer"},
    "GRANT_APPROVAL": {"user", "risk-owner"},
    "REJECT_APPROVAL": {"user", "risk-owner"},
    "REVOKE_APPROVAL": {"user", "risk-owner"},
    "INVALIDATE_APPROVAL": {"orchestrator"},
    "REGISTER_ARTIFACT": {"orchestrator", "rtl-engineer", "system-investigator", "verification-engineer"},
    "REGISTER_EVIDENCE": {"orchestrator", "system-investigator", "verification-engineer", "external-validator"},
    "CREATE_CLAIM": {"orchestrator", "system-investigator", "rtl-engineer", "verification-engineer"},
    "LINK_CLAIM_EVIDENCE": {"orchestrator", "system-investigator", "verification-engineer"},
    "SUPERSEDE_CLAIM": {"orchestrator", "system-investigator", "verification-engineer"},
    "SUBMIT_HANDOFF": {"orchestrator", "system-investigator", "rtl-engineer", "verification-engineer"},
    "ACCEPT_HANDOFF": {"verification-engineer", "integration-reviewer", "user"},
    "RECORD_ACCEPTANCE": {"integration-reviewer", "user", "risk-owner"},
    "CREATE_WAIVER": {"user", "risk-owner"},
    "CREATE_BLOCKER": {"orchestrator", "system-investigator", "rtl-engineer", "verification-engineer"},
    "RESOLVE_BLOCKER": {"orchestrator", "system-investigator", "rtl-engineer", "verification-engineer", "user"},
    "FINISH_TASK": {"orchestrator", "system-investigator", "rtl-engineer", "verification-engineer"},
    "REQUEST_REWORK": {"integration-reviewer", "verification-engineer", "orchestrator"},
    "REQUEST_CLOSURE": {"orchestrator", "integration-reviewer"},
    "CLOSE_TASK": {"orchestrator", "integration-reviewer", "user"},
    "CANCEL_TASK": {"orchestrator", "user"},
    "RECORD_DECISION": {"orchestrator", "documenter", "user"},
    "SET_GATE_STATUS": set(),
    "SET_CLAIM_STATUS": set(),
    "SET_CLOSURE_STATUS": set(),
    "SET_PROJECT_STATUS": set(),
}

DERIVED_WRITE_COMMANDS = {"SET_GATE_STATUS", "SET_CLAIM_STATUS", "SET_CLOSURE_STATUS", "SET_PROJECT_STATUS"}
REQUIRED_GATES = ("root_cause_gate", "implementation_gate", "simulation_gate", "integration_gate", "record_gate")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy(value: Any) -> Any:
    return deepcopy(value)


class Runtime:
    """Contract Runtime public seam: all mutations enter through dispatch()."""

    def __init__(self, event_store: JsonlEventStore | None = None, snapshot_path: str | Path | None = None):
        self.event_store = event_store or JsonlEventStore()
        self.snapshot_path = Path(snapshot_path) if snapshot_path is not None else None
        self.state: dict[str, dict[str, dict[str, Any]]] = {
            "Task": {},
            "Baseline": {},
            "Approval": {},
            "Artifact": {},
            "Evidence": {},
            "Claim": {},
            "Handoff": {},
            "Acceptance": {},
            "Waiver": {},
            "Blocker": {},
            "ClosureGate": {},
        }
        self._replay()

    def _replay(self) -> None:
        for record in self.event_store.events():
            self._apply_event(record["event"])
        self._recompute_all()

    def dispatch(self, command: dict[str, Any]) -> dict[str, Any]:
        self._validate_command(command)
        command_id = command["command_id"]
        previous = self.event_store.result_for(command_id)
        if previous is not None:
            return previous
        command_type = command["command_type"]
        if command_type in DERIVED_WRITE_COMMANDS:
            self._reject("DERIVED_RESULT_WRITE_FORBIDDEN", f"{command_type} is not a writable Command")
        allowed = ROLE_RULES.get(command_type)
        if allowed is None:
            self._reject("COMMAND_UNKNOWN", f"Unknown command: {command_type}")
        if command["actor"] not in allowed:
            self._reject("OWNERSHIP_VIOLATION", f"{command['actor']} cannot execute {command_type}")

        handler = getattr(self, f"_command_{command_type.lower()}", None)
        if handler is None:
            self._reject("COMMAND_NOT_IMPLEMENTED", f"Command is not implemented: {command_type}")
        event = handler(command)
        self._apply_event(event)
        self._recompute_all()
        target_id = self._target_id(command) or event["aggregate_id"]
        result = {
            "accepted": True,
            "command_id": command_id,
            "event": _copy(event),
            "object": self._query_any(target_id),
        }
        task_id = self._task_id_for_target(target_id)
        if task_id:
            result["task"] = self.query(task_id)
        self.event_store.append(command_id, event, result)
        return result

    def query(self, object_id: str, object_type: str | None = None) -> dict[str, Any]:
        value = self._query_any(object_id, object_type)
        if value is None:
            self._reject("OBJECT_NOT_FOUND", f"Object not found: {object_id}")
        return value

    def save_snapshot(self, path: str | Path | None = None) -> Path:
        destination = Path(path or self.snapshot_path or "runtime.snapshot.json")
        payload = {"schema_version": SCHEMA_VERSION, "last_sequence": self.event_store.last_sequence(), "state": self.state}
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(__import__("json").dumps(payload, sort_keys=True, ensure_ascii=False, indent=2), encoding="utf-8")
        return destination

    @classmethod
    def restore(cls, event_store: JsonlEventStore, snapshot_path: str | Path | None = None) -> "Runtime":
        runtime = cls(event_store, snapshot_path)
        if snapshot_path and Path(snapshot_path).exists():
            import json

            snapshot = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
            if snapshot.get("schema_version") != SCHEMA_VERSION:
                runtime._reject("SCHEMA_VERSION_UNSUPPORTED", "Snapshot schema version is unsupported")
            if snapshot.get("last_sequence") != event_store.last_sequence():
                runtime._reject("SNAPSHOT_SEQUENCE_CONFLICT", "Snapshot does not cover the current event sequence")
            if snapshot.get("state") != runtime.state:
                runtime._reject("SNAPSHOT_STATE_CONFLICT", "Snapshot conflicts with event replay")
        return runtime

    def _validate_command(self, command: dict[str, Any]) -> None:
        if not isinstance(command, dict):
            self._reject("COMMAND_INVALID", "Command must be an object")
        for field in ("command_id", "command_type", "actor"):
            if not isinstance(command.get(field), str) or not command[field]:
                self._reject("COMMAND_FIELD_MISSING", f"Missing command field: {field}")
        if not isinstance(command.get("payload", {}), dict):
            self._reject("COMMAND_PAYLOAD_INVALID", "payload must be an object")

    def _reject(self, code: str, message: str, *, details: dict[str, Any] | None = None):
        raise ContractError(code, message, details=details)

    def _base_object(self, object_type: str, object_id: str, actor: str, **fields: Any) -> dict[str, Any]:
        value = {
            "object_id": object_id,
            "object_type": object_type,
            "schema_version": SCHEMA_VERSION,
            "created_at": _now(),
            "created_by": actor,
            **fields,
        }
        validate_object(value)
        return value

    def _event(self, event_type: str, actor: str, aggregate_type: str, aggregate_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_id": f"event-{uuid4().hex}",
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "actor": actor,
            "occurred_at": _now(),
            "payload": _copy(payload),
        }

    def _target_id(self, command: dict[str, Any]) -> str:
        target = command.get("target_ref", "")
        if isinstance(target, dict):
            return target.get("object_id", "")
        return target

    def _task_id_for_target(self, object_id: str) -> str | None:
        if object_id in self.state["Task"]:
            return object_id
        for objects in self.state.values():
            value = objects.get(object_id)
            if value and value.get("task_ref"):
                return value["task_ref"]
        return None

    def _task(self, task_id: str) -> dict[str, Any]:
        task = self.state["Task"].get(task_id)
        if task is None:
            self._reject("OBJECT_NOT_FOUND", f"Task not found: {task_id}")
        return task

    def _baseline(self, task: dict[str, Any]) -> dict[str, Any]:
        baseline_id = task.get("baseline_ref")
        if not baseline_id or baseline_id not in self.state["Baseline"]:
            self._reject("BASELINE_REQUIRED", "Task must be bound to a Baseline")
        return self.state["Baseline"][baseline_id]

    def _required_approval_missing(self, task: dict[str, Any]) -> bool:
        required = set(task.get("required_capabilities", []))
        if not required.intersection({"WRITE", "EXTERNAL_DEVICE_ACCESS", "DESTRUCTIVE_OPERATION"}):
            return False
        baseline_id = task.get("baseline_ref")
        for approval in self.state["Approval"].values():
            if approval.get("task_ref") != task["object_id"] or approval.get("status") != "GRANTED":
                continue
            if approval.get("baseline_ref") != baseline_id:
                continue
            if approval.get("requested_capability") in required:
                return False
        return True

    def _gate_types(self, task: dict[str, Any]) -> list[tuple[str, bool]]:
        risks = set(task.get("risk_factors", []))
        gates = [(gate, True) for gate in REQUIRED_GATES]
        if "PROTOCOL_BEHAVIOR_CHANGE" in risks:
            gates.append(("protocol_gate", True))
        if "HARDWARE_STATE_CHANGE" in risks:
            gates.extend([("hardware_gate", True), ("risk_acceptance_gate", True)])
        return gates

    def _gate_objects(self, task: dict[str, Any], actor: str) -> list[dict[str, Any]]:
        return [
            self._base_object("ClosureGate", f"{task['object_id']}:{gate_type}", actor, task_ref=task["object_id"], gate_type=gate_type, required=required, dependency_refs=[])
            for gate_type, required in self._gate_types(task)
        ]

    def _command_create_task(self, command: dict[str, Any]) -> dict[str, Any]:
        payload = command["payload"]
        task_id = payload.get("task_id") or f"task-{uuid4().hex[:10]}"
        if task_id in self.state["Task"]:
            self._reject("DUPLICATE_OBJECT_ID", f"Task already exists: {task_id}")
        task = self._base_object(
            "Task", task_id, command["actor"], parent_task_ref=payload.get("parent_task_ref"), goal=payload.get("goal", ""),
            task_kind=None, primary_domain=None, domains=[], risk_factors=[], required_capabilities=[],
            execution_mode=None, scope=command.get("scope", {"paths": []}), task_owner="orchestrator",
            baseline_ref=None, execution_status="PROPOSED", blocker_refs=[], approval_refs=[], handoff_refs=[],
            artifact_refs=[], evidence_refs=[], claim_refs=[], gate_refs=[], record_gate="PENDING", closed_at=None,
        )
        return self._event("TASK_CREATED", command["actor"], "Task", task_id, {"object": task})

    def _command_classify_task(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        payload = command["payload"]
        required = ("task_kind", "primary_domain", "domains", "risk_factors", "required_capabilities", "execution_mode", "scope")
        for field in required:
            if field not in payload:
                self._reject("REQUIRED_FIELD_MISSING", f"Classification missing: {field}")
        task.update({field: _copy(payload[field]) for field in required})
        if task["execution_mode"] not in {"DIRECT", "ROUTED", "ORCHESTRATED"}:
            self._reject("INVALID_ENUM", "Invalid execution_mode")
        task["execution_status"] = "READY" if task.get("baseline_ref") else "PROPOSED"
        gates = self._gate_objects(task, command["actor"])
        task["gate_refs"] = [gate["object_id"] for gate in gates]
        return self._event("TASK_CLASSIFIED", command["actor"], "Task", task["object_id"], {"object": task, "gates": gates})

    def _command_propose_risk(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        risk_factor = command["payload"].get("risk_factor")
        if not risk_factor:
            self._reject("REQUIRED_FIELD_MISSING", "risk_factor is required")
        proposals = [*task.get("risk_proposals", [])]
        if risk_factor not in proposals and risk_factor not in task.get("risk_factors", []):
            proposals.append(risk_factor)
        task["risk_proposals"] = proposals
        return self._event("RISK_PROPOSED", command["actor"], "Task", task["object_id"], {"object": task, "risk_factor": risk_factor})

    def _command_activate_risk(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        risk_factor = command["payload"].get("risk_factor")
        if risk_factor not in task.get("risk_proposals", []):
            self._reject("RISK_NOT_PROPOSED", "Risk must be proposed before activation")
        task["risk_factors"] = [*task.get("risk_factors", [])]
        if risk_factor not in task["risk_factors"]:
            task["risk_factors"].append(risk_factor)
        if risk_factor == "PROTOCOL_BEHAVIOR_CHANGE" and "WRITE" not in task.get("required_capabilities", []):
            task["required_capabilities"] = [*task.get("required_capabilities", []), "WRITE"]
        task["risk_proposals"] = [risk for risk in task.get("risk_proposals", []) if risk != risk_factor]
        task["execution_status"] = "AWAITING_APPROVAL"
        approval_updates = []
        for approval in self.state["Approval"].values():
            if approval.get("task_ref") == task["object_id"] and approval.get("status") == "GRANTED":
                changed = _copy(approval)
                changed["status"] = "INVALIDATED"
                changed["invalidation_reason"] = f"NEW_RISK:{risk_factor}"
                approval_updates.append(changed)
        existing_gate_types = {gate["gate_type"] for gate in self.state["ClosureGate"].values() if gate.get("task_ref") == task["object_id"]}
        new_gates = []
        for gate_type, required in self._gate_types(task):
            if gate_type not in existing_gate_types:
                new_gates.append(self._base_object("ClosureGate", f"{task['object_id']}:{gate_type}", command["actor"], task_ref=task["object_id"], gate_type=gate_type, required=required, dependency_refs=[]))
        task["gate_refs"] = [*task.get("gate_refs", []), *[gate["object_id"] for gate in new_gates]]
        return self._event("RISK_ACTIVATED", command["actor"], "Task", task["object_id"], {"object": task, "approval_updates": approval_updates, "gates": new_gates, "risk_factor": risk_factor})

    def _make_baseline(self, command: dict[str, Any], baseline_id: str) -> dict[str, Any]:
        payload = command["payload"]
        return self._base_object(
            "Baseline", baseline_id, command["actor"], code_revision_or_workspace_snapshot=payload.get("code_revision_or_workspace_snapshot", ""),
            configuration_set=payload.get("configuration_set", {}), toolchain_versions=payload.get("toolchain_versions", {}),
            input_data_refs=payload.get("input_data_refs", []), dependency_refs=payload.get("dependency_refs", []), validity="VALID",
        )

    def _command_bind_baseline(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        baseline_id = command["payload"].get("baseline_id") or f"baseline-{uuid4().hex[:10]}"
        if baseline_id in self.state["Baseline"]:
            self._reject("DUPLICATE_OBJECT_ID", f"Baseline already exists: {baseline_id}")
        baseline = self._make_baseline(command, baseline_id)
        task["baseline_ref"] = baseline_id
        if task.get("task_kind") and task.get("primary_domain"):
            task["execution_status"] = "READY"
        return self._event("BASELINE_BOUND", command["actor"], "Task", task["object_id"], {"object": task, "baseline": baseline})

    def _command_change_baseline(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        old_id = task.get("baseline_ref")
        baseline_id = command["payload"].get("baseline_id") or f"baseline-{uuid4().hex[:10]}"
        if baseline_id in self.state["Baseline"]:
            self._reject("DUPLICATE_OBJECT_ID", f"Baseline already exists: {baseline_id}")
        baseline = self._make_baseline(command, baseline_id)
        task["baseline_ref"] = baseline_id
        evidence_updates = []
        for evidence in self.state["Evidence"].values():
            if evidence.get("task_ref") == task["object_id"] and evidence.get("baseline_ref") == old_id:
                changed = _copy(evidence)
                changed["invalidated_by"] = baseline_id
                evidence_updates.append(changed)
        approval_updates = []
        for approval in self.state["Approval"].values():
            if approval.get("task_ref") == task["object_id"] and approval.get("status") == "GRANTED":
                changed = _copy(approval)
                changed["status"] = "INVALIDATED"
                changed["invalidation_reason"] = "BASELINE_CHANGED"
                approval_updates.append(changed)
        claim_updates = []
        for claim in self.state["Claim"].values():
            if claim.get("task_ref") == task["object_id"] and claim.get("baseline_ref") == old_id:
                changed = _copy(claim)
                changed["invalidated_by"] = baseline_id
                claim_updates.append(changed)
        task["execution_status"] = "AWAITING_APPROVAL" if approval_updates else task["execution_status"]
        return self._event("BASELINE_CHANGED", command["actor"], "Task", task["object_id"], {"object": task, "baseline": baseline, "evidence_updates": evidence_updates, "approval_updates": approval_updates, "claim_updates": claim_updates})

    def _command_start_task(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        self._baseline(task)
        if task["execution_status"] not in {"READY", "AWAITING_APPROVAL", "REWORK_REQUIRED"}:
            self._reject("INVALID_STATE", f"Cannot start from {task['execution_status']}")
        if self._active_blockers(task["object_id"]):
            self._reject("BLOCKER_ACTIVE", "Task has an active Blocker")
        if self._required_approval_missing(task):
            task["execution_status"] = "AWAITING_APPROVAL"
            return self._event("TASK_AWAITING_APPROVAL", command["actor"], "Task", task["object_id"], {"object": task, "reason": "APPROVAL_REQUIRED"})
        task["execution_status"] = "RUNNING"
        return self._event("TASK_STARTED", command["actor"], "Task", task["object_id"], {"object": task})

    def _command_request_approval(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        payload = command["payload"]
        approval_id = payload.get("approval_id") or f"approval-{uuid4().hex[:10]}"
        if approval_id in self.state["Approval"]:
            self._reject("DUPLICATE_OBJECT_ID", f"Approval already exists: {approval_id}")
        approval = self._base_object("Approval", approval_id, command["actor"], task_ref=task["object_id"], requested_capability=payload.get("requested_capability"), risk_factors=payload.get("risk_factors", []), requested_scope=payload.get("requested_scope", command.get("scope", {})), baseline_ref=payload.get("baseline_ref") or task.get("baseline_ref"), status="REQUESTED", decision_basis=None, invalidation_reason=None)
        task["approval_refs"] = [*task.get("approval_refs", []), approval_id]
        task["execution_status"] = "AWAITING_APPROVAL"
        return self._event("APPROVAL_REQUESTED", command["actor"], "Task", task["object_id"], {"object": approval, "task": task})

    def _command_grant_approval(self, command: dict[str, Any]) -> dict[str, Any]:
        approval = _copy(self.state["Approval"].get(self._target_id(command)))
        if approval is None:
            self._reject("OBJECT_NOT_FOUND", "Approval not found")
        if approval["status"] != "REQUESTED":
            self._reject("INVALID_STATE", "Only REQUESTED approval can be granted")
        approval["status"] = "GRANTED"
        approval["decision_basis"] = command["payload"].get("decision_basis", "")
        task = _copy(self._task(approval["task_ref"]))
        task["execution_status"] = "READY" if not self._required_approval_missing_after(task, approval) else "AWAITING_APPROVAL"
        return self._event("APPROVAL_GRANTED", command["actor"], "Approval", approval["object_id"], {"object": approval, "task": task})

    def _required_approval_missing_after(self, task: dict[str, Any], candidate: dict[str, Any]) -> bool:
        required = set(task.get("required_capabilities", []))
        if not required.intersection({"WRITE", "EXTERNAL_DEVICE_ACCESS", "DESTRUCTIVE_OPERATION"}):
            return False
        return candidate.get("requested_capability") not in required

    def _command_reject_approval(self, command: dict[str, Any]) -> dict[str, Any]:
        return self._approval_decision(command, "REJECTED")

    def _command_revoke_approval(self, command: dict[str, Any]) -> dict[str, Any]:
        return self._approval_decision(command, "REVOKED")

    def _command_invalidate_approval(self, command: dict[str, Any]) -> dict[str, Any]:
        return self._approval_decision(command, "INVALIDATED")

    def _approval_decision(self, command: dict[str, Any], status: str) -> dict[str, Any]:
        approval = _copy(self.state["Approval"].get(self._target_id(command)))
        if approval is None:
            self._reject("OBJECT_NOT_FOUND", "Approval not found")
        approval["status"] = status
        approval["invalidation_reason"] = command["payload"].get("reason", status)
        task = _copy(self._task(approval["task_ref"]))
        task["execution_status"] = "AWAITING_APPROVAL"
        artifact_updates = []
        if status in {"REVOKED", "INVALIDATED"}:
            for artifact in self.state["Artifact"].values():
                if artifact.get("task_ref") == task["object_id"]:
                    changed = _copy(artifact)
                    changed["review_required"] = True
                    artifact_updates.append(changed)
        return self._event(f"APPROVAL_{status}", command["actor"], "Approval", approval["object_id"], {"object": approval, "task": task, "artifact_updates": artifact_updates})

    def _command_register_artifact(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        baseline = self._baseline(task)
        payload = command["payload"]
        if payload.get("artifact_type") in {"rtl_patch", "implementation", "rtl_change"} and self._required_approval_missing(task):
            self._reject("APPROVAL_REQUIRED", "Formal implementation Artifact requires a current WRITE Approval")
        artifact_id = payload.get("artifact_id") or f"artifact-{uuid4().hex[:10]}"
        if artifact_id in self.state["Artifact"]:
            self._reject("DUPLICATE_OBJECT_ID", f"Artifact already exists: {artifact_id}")
        scope = payload.get("scope", command.get("scope", {}))
        if self._scope_conflicts(scope, task["object_id"]):
            self._reject("SCOPE_CONFLICT", "A different task already owns an overlapping write Scope")
        artifact = self._base_object("Artifact", artifact_id, command["actor"], task_ref=task["object_id"], artifact_type=payload.get("artifact_type", ""), location=payload.get("location", ""), producer=command["actor"], baseline_ref=payload.get("baseline_ref") or baseline["object_id"], dependency_refs=payload.get("dependency_refs", []), scope=scope, validity="VALID", invalidated_by=None, review_required=False)
        if artifact["baseline_ref"] != baseline["object_id"]:
            self._reject("BASELINE_MISMATCH", "Artifact must use the current Task Baseline")
        task["artifact_refs"] = [*task.get("artifact_refs", []), artifact_id]
        return self._event("ARTIFACT_REGISTERED", command["actor"], "Artifact", artifact_id, {"object": artifact, "task": task})

    def _scope_conflicts(self, scope: dict[str, Any], task_id: str) -> bool:
        paths = {str(path).replace("\\", "/").rstrip("/") for path in scope.get("paths", [])}
        if not paths:
            return False
        for artifact in self.state["Artifact"].values():
            if artifact.get("task_ref") == task_id or artifact.get("validity") == "INVALIDATED":
                continue
            existing = {str(path).replace("\\", "/").rstrip("/") for path in artifact.get("scope", {}).get("paths", [])}
            if any(a == b or a.startswith(b + "/") or b.startswith(a + "/") for a in paths for b in existing):
                return True
        return False

    def _command_register_evidence(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        baseline = self._baseline(task)
        payload = command["payload"]
        evidence_id = payload.get("evidence_id") or f"evidence-{uuid4().hex[:10]}"
        if evidence_id in self.state["Evidence"]:
            self._reject("DUPLICATE_OBJECT_ID", f"Evidence already exists: {evidence_id}")
        for artifact_ref in payload.get("artifact_refs", []):
            artifact = self.state["Artifact"].get(artifact_ref)
            if artifact is None:
                self._reject("OBJECT_NOT_FOUND", f"Artifact not found: {artifact_ref}")
            if artifact.get("baseline_ref") != baseline["object_id"]:
                self._reject("BASELINE_MISMATCH", "Evidence Artifact is not on the current Baseline")
        evidence = self._base_object("Evidence", evidence_id, command["actor"], task_ref=task["object_id"], evidence_type=payload.get("evidence_type", ""), source=payload.get("source", command["actor"]), artifact_refs=payload.get("artifact_refs", []), execution_ref=payload.get("execution_ref"), baseline_ref=payload.get("baseline_ref") or baseline["object_id"], producer=command["actor"], produced_at=_now(), summary=payload.get("summary", ""), reproducibility_level=payload.get("reproducibility_level", "E0"), relevance=payload.get("relevance", ""), coverage=payload.get("coverage", ""), independence=payload.get("independence", ["SELF_PRODUCED"]), invalidated_by=None)
        if evidence["baseline_ref"] != baseline["object_id"]:
            self._reject("BASELINE_MISMATCH", "Evidence must use the current Task Baseline")
        task["evidence_refs"] = [*task.get("evidence_refs", []), evidence_id]
        return self._event("EVIDENCE_REGISTERED", command["actor"], "Evidence", evidence_id, {"object": evidence, "task": task})

    def _command_create_claim(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        self._baseline(task)
        payload = command["payload"]
        claim_id = payload.get("claim_id") or f"claim-{uuid4().hex[:10]}"
        if claim_id in self.state["Claim"]:
            self._reject("DUPLICATE_OBJECT_ID", f"Claim already exists: {claim_id}")
        claim = self._base_object("Claim", claim_id, command["actor"], task_ref=task["object_id"], statement=payload.get("statement", ""), claim_type=payload.get("claim_type", "HYPOTHESIS"), producer=command["actor"], scope=payload.get("scope", task.get("scope", {})), baseline_ref=payload.get("baseline_ref") or task["baseline_ref"], supported_by=[], contradicted_by=[], derived_from=payload.get("derived_from", []), supersedes=payload.get("supersedes"))
        if claim["baseline_ref"] != task["baseline_ref"]:
            self._reject("BASELINE_MISMATCH", "Claim must use the current Task Baseline")
        task["claim_refs"] = [*task.get("claim_refs", []), claim_id]
        return self._event("CLAIM_CREATED", command["actor"], "Claim", claim_id, {"object": claim, "task": task})

    def _command_link_claim_evidence(self, command: dict[str, Any]) -> dict[str, Any]:
        claim = _copy(self.state["Claim"].get(self._target_id(command)))
        if claim is None:
            self._reject("OBJECT_NOT_FOUND", "Claim not found")
        evidence_ref = command["payload"].get("evidence_ref")
        evidence = self.state["Evidence"].get(evidence_ref)
        if evidence is None:
            self._reject("OBJECT_NOT_FOUND", "Evidence not found")
        if evidence["baseline_ref"] != claim["baseline_ref"]:
            self._reject("BASELINE_MISMATCH", "Claim and Evidence must share a Baseline")
        relation = command["payload"].get("relation", "supports")
        if relation not in {"supports", "contradicts"}:
            self._reject("INVALID_ENUM", "relation must be supports or contradicts")
        field = "supported_by" if relation == "supports" else "contradicted_by"
        if evidence_ref not in claim[field]:
            claim[field].append(evidence_ref)
        return self._event("CLAIM_EVIDENCE_LINKED", command["actor"], "Claim", claim["object_id"], {"object": claim})

    def _command_supersede_claim(self, command: dict[str, Any]) -> dict[str, Any]:
        old = _copy(self.state["Claim"].get(self._target_id(command)))
        if old is None:
            self._reject("OBJECT_NOT_FOUND", "Claim not found")
        new_payload = command["payload"]
        task = self._task(old["task_ref"])
        new_claim = self._base_object("Claim", new_payload.get("claim_id") or f"claim-{uuid4().hex[:10]}", command["actor"], task_ref=task["object_id"], statement=new_payload.get("statement", ""), claim_type=new_payload.get("claim_type", "INFERENCE"), producer=command["actor"], scope=new_payload.get("scope", task.get("scope", {})), baseline_ref=task["baseline_ref"], supported_by=[], contradicted_by=[], derived_from=[old["object_id"]], supersedes=old["object_id"])
        task = _copy(task)
        task["claim_refs"] = [*task.get("claim_refs", []), new_claim["object_id"]]
        return self._event("CLAIM_SUPERSEDED", command["actor"], "Claim", old["object_id"], {"object": new_claim, "superseded_claim": old, "task": task})

    def _command_submit_handoff(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        self._baseline(task)
        payload = command["payload"]
        handoff_id = payload.get("handoff_id") or f"handoff-{uuid4().hex[:10]}"
        handoff = self._base_object("Handoff", handoff_id, command["actor"], task_ref=task["object_id"], source_role=command["actor"], target_role=payload.get("target_role", ""), scope=payload.get("scope", task.get("scope", {})), authorization_refs=payload.get("authorization_refs", []), baseline_ref=payload.get("baseline_ref") or task["baseline_ref"], context_package=payload.get("context_package", {}), artifact_refs=payload.get("artifact_refs", []), evidence_refs=payload.get("evidence_refs", []), claim_refs=payload.get("claim_refs", []), blocker_refs=payload.get("blocker_refs", []), expected_output=payload.get("expected_output", ""), completion_criteria=payload.get("completion_criteria", ""), acceptance_ref=None)
        task["handoff_refs"] = [*task.get("handoff_refs", []), handoff_id]
        return self._event("HANDOFF_SUBMITTED", command["actor"], "Handoff", handoff_id, {"object": handoff, "task": task})

    def _command_accept_handoff(self, command: dict[str, Any]) -> dict[str, Any]:
        handoff = _copy(self.state["Handoff"].get(self._target_id(command)))
        if handoff is None:
            self._reject("OBJECT_NOT_FOUND", "Handoff not found")
        acceptance = self._acceptance_object(command, "HANDOFF", handoff["object_id"], handoff["task_ref"])
        handoff["acceptance_ref"] = acceptance["object_id"]
        return self._event("HANDOFF_ACCEPTED", command["actor"], "Handoff", handoff["object_id"], {"object": handoff, "acceptance": acceptance})

    def _acceptance_object(self, command: dict[str, Any], target_type: str, target_ref: str, task_ref: str) -> dict[str, Any]:
        payload = command["payload"]
        baseline_ref = payload.get("baseline_ref") or self._task(task_ref).get("baseline_ref")
        return self._base_object("Acceptance", payload.get("acceptance_id") or f"acceptance-{uuid4().hex[:10]}", command["actor"], task_ref=task_ref, target_type=target_type, target_ref=target_ref, accepted_by=command["actor"], acceptance_scope=payload.get("acceptance_scope", ""), acceptance_basis=payload.get("acceptance_basis", ""), conditions=payload.get("conditions", []), baseline_ref=baseline_ref, acceptance_status=payload.get("acceptance_status", "ACCEPTED"), accepted_at=_now())

    def _command_record_acceptance(self, command: dict[str, Any]) -> dict[str, Any]:
        target_ref = self._target_id(command)
        target = self._query_any(target_ref)
        if target is None:
            self._reject("OBJECT_NOT_FOUND", "Acceptance target not found")
        target_type = command["payload"].get("target_type") or target["object_type"]
        if target_type == "RISK":
            self._reject("ACCEPTANCE_TARGET_INVALID", "Risk must use Waiver")
        if target_type not in {"HANDOFF", "ARTIFACT", "CLAIM", "TASK_RESULT"}:
            self._reject("ACCEPTANCE_TARGET_INVALID", "Unsupported Acceptance target")
        task_ref = target.get("task_ref") or (target_ref if target.get("object_type") == "Task" else None)
        if not task_ref:
            self._reject("TASK_REFERENCE_REQUIRED", "Acceptance target must resolve to a Task")
        if not command["payload"].get("acceptance_scope") or not command["payload"].get("acceptance_basis"):
            self._reject("ACCEPTANCE_BASIS_INCOMPLETE", "Acceptance scope and basis are required")
        acceptance = self._acceptance_object(command, target_type, target_ref, task_ref)
        return self._event("ACCEPTANCE_RECORDED", command["actor"], "Acceptance", acceptance["object_id"], {"object": acceptance})

    def _command_create_waiver(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        baseline = self._baseline(task)
        payload = command["payload"]
        if payload.get("baseline_ref", task["baseline_ref"]) != baseline["object_id"]:
            self._reject("BASELINE_MISMATCH", "Waiver must match the current Baseline")
        gate_type = payload.get("gate_type")
        gate_id = f"{task['object_id']}:{gate_type}"
        gate = self.state["ClosureGate"].get(gate_id)
        if gate is None:
            self._reject("OBJECT_NOT_FOUND", "Waiver target Gate not found")
        waiver = self._base_object("Waiver", payload.get("waiver_id") or f"waiver-{uuid4().hex[:10]}", command["actor"], task_ref=task["object_id"], waived_subject=gate_id, risk_description=payload.get("risk_description", ""), scope=payload.get("scope", task.get("scope", {})), baseline_ref=baseline["object_id"], accepted_by=command["actor"], rationale=payload.get("rationale", ""), conditions=payload.get("conditions", []), validity=payload.get("validity", "current-baseline"), created_at=_now())
        gate = _copy(gate)
        gate["waiver_ref"] = waiver["object_id"]
        return self._event("WAIVER_CREATED", command["actor"], "Waiver", waiver["object_id"], {"object": waiver, "gate": gate})

    def _command_create_blocker(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        payload = command["payload"]
        blocker = self._base_object("Blocker", payload.get("blocker_id") or f"blocker-{uuid4().hex[:10]}", command["actor"], task_ref=task["object_id"], blocker_type=payload.get("blocker_type", "CONTRACT_FAILURE"), blocker_owner=payload.get("blocker_owner", command["actor"]), description=payload.get("description", ""), required_action=payload.get("required_action", ""), resume_condition=payload.get("resume_condition", ""), affected_refs=payload.get("affected_refs", []), resolved=False, resolved_at=None)
        task["blocker_refs"] = [*task.get("blocker_refs", []), blocker["object_id"]]
        task["execution_status"] = "BLOCKED"
        return self._event("BLOCKER_CREATED", command["actor"], "Blocker", blocker["object_id"], {"object": blocker, "task": task})

    def _command_resolve_blocker(self, command: dict[str, Any]) -> dict[str, Any]:
        blocker = _copy(self.state["Blocker"].get(self._target_id(command)))
        if blocker is None:
            self._reject("OBJECT_NOT_FOUND", "Blocker not found")
        if not blocker.get("resume_condition"):
            self._reject("RESUME_CONDITION_MISSING", "Blocker has no resume condition")
        blocker["resolved"] = True
        blocker["resolved_at"] = _now()
        task = _copy(self._task(blocker["task_ref"]))
        task["execution_status"] = command["payload"].get("resume_status", "RUNNING")
        return self._event("BLOCKER_RESOLVED", command["actor"], "Blocker", blocker["object_id"], {"object": blocker, "task": task})

    def _command_finish_task(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        if task["execution_status"] not in {"RUNNING", "AWAITING_VALIDATION", "REWORK_REQUIRED"}:
            self._reject("INVALID_STATE", "Task cannot finish from current state")
        task["execution_status"] = "FINISHED"
        return self._event("TASK_FINISHED", command["actor"], "Task", task["object_id"], {"object": task})

    def _command_request_rework(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        task["execution_status"] = "REWORK_REQUIRED"
        return self._event("TASK_REWORK_REQUESTED", command["actor"], "Task", task["object_id"], {"object": task})

    def _command_request_closure(self, command: dict[str, Any]) -> dict[str, Any]:
        task = self._task(self._target_id(command))
        if self._closure_status(task) != "CLOSABLE":
            self._reject("CLOSURE_NOT_READY", "Required Gate, Acceptance, Blocker or record gate is incomplete")
        return self._event("TASK_CLOSURE_REQUESTED", command["actor"], "Task", task["object_id"], {"object": _copy(task)})

    def _command_close_task(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        if self._closure_status(task) != "CLOSABLE":
            self._reject("CLOSURE_NOT_READY", "Task is not CLOSABLE")
        task["closed_at"] = _now()
        task["execution_status"] = "FINISHED"
        return self._event("TASK_CLOSED", command["actor"], "Task", task["object_id"], {"object": task})

    def _command_cancel_task(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        task["execution_status"] = "CANCELLED"
        return self._event("TASK_CANCELLED", command["actor"], "Task", task["object_id"], {"object": task})

    def _command_record_decision(self, command: dict[str, Any]) -> dict[str, Any]:
        task = _copy(self._task(self._target_id(command)))
        decision = command["payload"].get("decision")
        if decision not in {"written", "declined", "not_required"}:
            self._reject("INVALID_ENUM", "Invalid record decision")
        task["record_gate"] = "RESOLVED"
        task["record_decision"] = decision
        return self._event("RECORD_DECISION_RECORDED", command["actor"], "Task", task["object_id"], {"object": task})

    def _apply_event(self, event: dict[str, Any]) -> None:
        event_type = event["event_type"]
        payload = event.get("payload", {})
        object_value = payload.get("object")
        if object_value:
            self.state[object_value["object_type"]][object_value["object_id"]] = _copy(object_value)
        if payload.get("baseline"):
            baseline = payload["baseline"]
            self.state["Baseline"][baseline["object_id"]] = _copy(baseline)
        task = payload.get("task")
        if task:
            self.state["Task"][task["object_id"]] = _copy(task)
        if event_type == "TASK_CLASSIFIED":
            for gate in payload.get("gates", []):
                self.state["ClosureGate"][gate["object_id"]] = _copy(gate)
        if event_type == "RISK_ACTIVATED":
            for gate in payload.get("gates", []):
                self.state["ClosureGate"][gate["object_id"]] = _copy(gate)
            for update in payload.get("approval_updates", []):
                self.state["Approval"][update["object_id"]] = _copy(update)
        if event_type == "BASELINE_CHANGED":
            for update in payload.get("evidence_updates", []):
                self.state["Evidence"][update["object_id"]] = _copy(update)
            for update in payload.get("approval_updates", []):
                self.state["Approval"][update["object_id"]] = _copy(update)
            for update in payload.get("claim_updates", []):
                self.state["Claim"][update["object_id"]] = _copy(update)
        if event_type == "CLAIM_SUPERSEDED":
            superseded = payload.get("superseded_claim")
            if superseded:
                superseded = _copy(superseded)
                superseded["superseded_by"] = object_value["object_id"] if object_value else None
                self.state["Claim"][superseded["object_id"]] = superseded
        if event_type.startswith("APPROVAL_"):
            for update in payload.get("artifact_updates", []):
                self.state["Artifact"][update["object_id"]] = _copy(update)
        if payload.get("acceptance"):
            acceptance = payload["acceptance"]
            self.state["Acceptance"][acceptance["object_id"]] = _copy(acceptance)
        if payload.get("gate"):
            gate = payload["gate"]
            self.state["ClosureGate"][gate["object_id"]] = _copy(gate)

    def _recompute_all(self) -> None:
        return

    def _query_any(self, object_id: str, object_type: str | None = None) -> dict[str, Any] | None:
        if object_type:
            value = self.state.get(object_type, {}).get(object_id)
            return self._derived_object(value) if value else None
        for values in self.state.values():
            if object_id in values:
                return self._derived_object(values[object_id])
        return None

    def _derived_object(self, value: dict[str, Any]) -> dict[str, Any]:
        result = _copy(value)
        object_type = result["object_type"]
        if object_type == "Task":
            result["acceptance_summary"] = self._acceptance_summary(result)
            result["closure_status"] = self._closure_status(result)
            result["gates"] = self._gate_views(result)
        elif object_type == "Claim":
            result["status"] = self._claim_status(result)
        elif object_type == "Evidence":
            result["validity"] = "INVALIDATED" if result.get("invalidated_by") else "VALID"
        elif object_type == "Artifact":
            result["validity"] = "INVALIDATED" if result.get("invalidated_by") else "VALID"
        elif object_type == "ClosureGate":
            result["status"] = self._gate_status(result)
        elif object_type == "Handoff":
            result["acceptance_status"] = self._handoff_acceptance_status(result)
        return result

    def _acceptance_summary(self, task: dict[str, Any]) -> dict[str, Any]:
        values = [a for a in self.state["Acceptance"].values() if a.get("task_ref") == task["object_id"]]
        handoff = [a for a in values if a.get("target_type") == "HANDOFF"]
        technical = [a for a in values if a.get("target_type") != "HANDOFF"]
        return {"handoff_acceptance": self._summary_status(handoff), "technical_acceptance": self._summary_status(technical)}

    @staticmethod
    def _summary_status(values: list[dict[str, Any]]) -> str:
        if not values:
            return "NOT_REVIEWED"
        if any(value.get("acceptance_status") == "REJECTED" for value in values):
            return "REJECTED"
        if any(value.get("acceptance_status") == "CONDITIONALLY_ACCEPTED" for value in values):
            return "CONDITIONALLY_ACCEPTED"
        return "ACCEPTED" if all(value.get("acceptance_status") == "ACCEPTED" for value in values) else "NOT_REVIEWED"

    def _handoff_acceptance_status(self, handoff: dict[str, Any]) -> str:
        ref = handoff.get("acceptance_ref")
        if not ref:
            return "NOT_REVIEWED"
        acceptance = self.state["Acceptance"].get(ref)
        return acceptance.get("acceptance_status", "NOT_REVIEWED") if acceptance else "NOT_REVIEWED"

    def _claim_status(self, claim: dict[str, Any]) -> str:
        if claim.get("invalidated_by"):
            return "INVALIDATED"
        if claim.get("superseded_by"):
            return "SUPERSEDED"
        contradictions = [self.state["Evidence"].get(ref) for ref in claim.get("contradicted_by", [])]
        if any(evidence and not evidence.get("invalidated_by") for evidence in contradictions):
            return "CONTRADICTED"
        supports = [self.state["Evidence"].get(ref) for ref in claim.get("supported_by", [])]
        if any(evidence and not evidence.get("invalidated_by") for evidence in supports):
            return "SUPPORTED"
        return "PROPOSED"

    def _gate_views(self, task: dict[str, Any]) -> list[dict[str, Any]]:
        return [self._derived_object(gate) for gate in self.state["ClosureGate"].values() if gate.get("task_ref") == task["object_id"]]

    def _gate_status(self, gate: dict[str, Any]) -> str:
        if not gate.get("required", True):
            return "NOT_REQUIRED"
        if gate.get("waiver_ref"):
            waiver = self.state["Waiver"].get(gate["waiver_ref"])
            if waiver and waiver.get("baseline_ref") == self._task(gate["task_ref"]).get("baseline_ref"):
                return "WAIVED"
        task = self._task(gate["task_ref"])
        gate_type = gate["gate_type"]
        if gate_type == "root_cause_gate":
            return "SATISFIED" if any(self._claim_status(claim) == "SUPPORTED" for claim in self.state["Claim"].values() if claim.get("task_ref") == task["object_id"]) else "UNSATISFIED"
        if gate_type == "implementation_gate":
            return "SATISFIED" if any(a.get("task_ref") == task["object_id"] and not a.get("invalidated_by") and a.get("artifact_type") in {"rtl_patch", "implementation", "rtl_change"} for a in self.state["Artifact"].values()) else "UNSATISFIED"
        if gate_type == "simulation_gate":
            return "SATISFIED" if any(e.get("task_ref") == task["object_id"] and not e.get("invalidated_by") and e.get("evidence_type") in {"simulation", "reproduction", "python_reference", "protocol_regression"} for e in self.state["Evidence"].values()) else "UNSATISFIED"
        if gate_type == "protocol_gate":
            return "SATISFIED" if any(e.get("task_ref") == task["object_id"] and not e.get("invalidated_by") and e.get("evidence_type") == "protocol_regression" for e in self.state["Evidence"].values()) else "UNSATISFIED"
        if gate_type == "integration_gate":
            return "SATISFIED" if any(a.get("task_ref") == task["object_id"] and a.get("target_type") in {"TASK_RESULT", "ARTIFACT", "CLAIM"} and a.get("acceptance_status") in {"ACCEPTED", "CONDITIONALLY_ACCEPTED"} for a in self.state["Acceptance"].values()) else "UNSATISFIED"
        if gate_type == "record_gate":
            return "SATISFIED" if task.get("record_gate") == "RESOLVED" else "UNSATISFIED"
        if gate_type == "risk_acceptance_gate":
            return "UNSATISFIED"
        if gate_type == "hardware_gate":
            return "SATISFIED" if any(e.get("task_ref") == task["object_id"] and not e.get("invalidated_by") and e.get("evidence_type") == "hardware" and "EXTERNAL_SOURCE" in e.get("independence", []) for e in self.state["Evidence"].values()) else "UNSATISFIED"
        return "UNSATISFIED"

    def _active_blockers(self, task_id: str) -> list[dict[str, Any]]:
        return [blocker for blocker in self.state["Blocker"].values() if blocker.get("task_ref") == task_id and not blocker.get("resolved")]

    def _closure_status(self, task: dict[str, Any]) -> str:
        if task.get("closed_at"):
            return "CLOSED"
        if task.get("record_gate") != "RESOLVED":
            return "OPEN"
        if self._active_blockers(task["object_id"]):
            return "OPEN"
        children = [child for child in self.state["Task"].values() if child.get("parent_task_ref") == task["object_id"]]
        if any(self._closure_status(child) not in {"CLOSABLE", "CLOSED"} for child in children):
            return "OPEN"
        if self._acceptance_summary(task)["technical_acceptance"] not in {"ACCEPTED", "CONDITIONALLY_ACCEPTED"}:
            return "OPEN"
        if all(view["status"] in {"SATISFIED", "WAIVED", "NOT_REQUIRED"} for view in self._gate_views(task)):
            return "CLOSABLE"
        return "OPEN"
