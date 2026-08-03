"""End-to-end bridge tests driving a real subprocess over stdio JSONL."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class BridgeProcess:
    def __init__(self, state_dir: Path, config: dict | None = None):
        state_dir.mkdir(parents=True, exist_ok=True)
        if config is not None:
            (state_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "runtime.omp_bridge", "--stdio", "--state-dir", str(state_dir)],
            cwd=REPO_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        self.seq = 0

    def request(self, op: str, params: dict | None = None, *, expect_ok: bool = True):
        self.seq += 1
        request_id = f"t{self.seq}"
        self.proc.stdin.write(json.dumps({"id": request_id, "op": op, "params": params or {}}) + "\n")
        self.proc.stdin.flush()
        frame = json.loads(self.proc.stdout.readline())
        assert frame["id"] == request_id
        if expect_ok:
            assert frame["ok"], frame
            return frame["result"]
        assert not frame["ok"], frame
        return frame["error"]

    def raw(self, line: str):
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def stop(self):
        if self.proc.poll() is None:
            self.request("shutdown")
            self.proc.wait(timeout=10)


def create_started_task(bridge, *, task_id="task-m3", scope_paths=("pilot/rtl",)):
    bridge.request("dispatch", {"command": {"command_id": f"{task_id}-create", "command_type": "CREATE_TASK", "actor": "orchestrator", "payload": {"task_id": task_id, "goal": "Milestone 3 pilot"}}})
    bridge.request("dispatch", {"command": {"command_id": f"{task_id}-classify", "command_type": "CLASSIFY_TASK", "actor": "orchestrator", "target_ref": {"object_id": task_id}, "payload": {"task_kind": "investigation", "primary_domain": "qspi", "domains": ["rtl"], "risk_factors": [], "required_capabilities": ["WRITE"], "execution_mode": "ORCHESTRATED", "scope": {"paths": list(scope_paths)}}}})
    bridge.request("dispatch", {"command": {"command_id": f"{task_id}-baseline", "command_type": "BIND_BASELINE", "actor": "orchestrator", "target_ref": {"object_id": task_id}, "payload": {"baseline_id": "baseline-a", "code_revision_or_workspace_snapshot": "abc123", "configuration_set": {}, "toolchain_versions": {"python": "3.11"}, "input_data_refs": []}}})
    return bridge.request("query", {"object_id": task_id})["object"]


def grant_write_approval(bridge, task_id="task-m3"):
    bridge.request("dispatch", {"command": {"command_id": "req-1", "command_type": "REQUEST_APPROVAL", "actor": "orchestrator", "target_ref": {"object_id": task_id}, "payload": {"approval_id": "approval-1", "requested_capability": "WRITE", "risk_factors": [], "requested_scope": {"paths": ["pilot/rtl"]}}}})
    bridge.request("dispatch", {"command": {"command_id": "grant-1", "command_type": "GRANT_APPROVAL", "actor": "user", "target_ref": {"object_id": "approval-1"}, "payload": {"decision_basis": "test grant"}}})


def test_non_ascii_payload_round_trips_utf8(tmp_path):
    """Windows locale code pages (GBK) must not corrupt the UTF-8 JSONL protocol."""
    bridge = BridgeProcess(tmp_path / "state")
    try:
        goal = "Milestone 3 — OMP-Native Real Project Pilot（中文目标）"
        bridge.request("dispatch", {"command": {"command_id": "cmd-nonascii", "command_type": "CREATE_TASK", "actor": "orchestrator", "payload": {"task_id": "task-nonascii", "goal": goal}}})
        task = bridge.request("query", {"object_id": "task-nonascii"})["object"]
        assert task["goal"] == goal
        restored = BridgeProcess(tmp_path / "state")  # replay must preserve the goal
        try:
            task_after = restored.request("query", {"object_id": "task-nonascii"})["object"]
            assert task_after["goal"] == goal
        finally:
            restored.stop()
    finally:
        bridge.stop()


def test_hello_reports_contract_surface(tmp_path):
    bridge = BridgeProcess(tmp_path / "state")
    try:
        hello = bridge.request("hello")
        assert hello["protocol_version"] == 1
        assert set(hello["roles"]) == {"orchestrator", "system-investigator", "rtl-engineer", "verification-engineer", "integration-reviewer", "documenter"}
        assert "gate_status" in hello["forbidden_role_fields"]
        assert "approval_granted" in hello["forbidden_role_fields"]
        assert set(hello["role_request_fields"]) == {"role", "task_ref", "scope", "approval_refs", "baseline_ref", "expected_output", "completion_criteria"}
        assert hello["last_sequence"] == 0
    finally:
        bridge.stop()


def test_dispatch_flow_query_and_idempotency(tmp_path):
    bridge = BridgeProcess(tmp_path / "state")
    try:
        task = create_started_task(bridge)
        assert task["execution_status"] == "READY"
        assert task["baseline_ref"] == "baseline-a"
        # Idempotent retry of the same command_id returns the stored result.
        result = bridge.request("dispatch", {"command": {"command_id": "task-m3-create", "command_type": "CREATE_TASK", "actor": "orchestrator", "payload": {"task_id": "task-m3", "goal": "Milestone 3 pilot"}}})
        assert result["accepted"] is True
        status = bridge.request("status")
        assert [task["object_id"] for task in status["tasks"]] == ["task-m3"]
        assert status["next_legal_actions"]["task-m3"]
    finally:
        bridge.stop()


def test_derived_result_write_rejected(tmp_path):
    bridge = BridgeProcess(tmp_path / "state")
    try:
        error = bridge.request("dispatch", {"command": {"command_id": "bad-1", "command_type": "SET_GATE_STATUS", "actor": "orchestrator", "payload": {}}}, expect_ok=False)
        assert error["code"] == "DERIVED_RESULT_WRITE_FORBIDDEN"
    finally:
        bridge.stop()


def test_guard_blocks_then_allows_after_approval_then_blocks_after_revoke(tmp_path):
    bridge = BridgeProcess(tmp_path / "state")
    try:
        create_started_task(bridge)
        denied = bridge.request("guard_check", {"tool_name": "edit", "paths": ["pilot/rtl/a.v"]})
        assert denied["allowed"] is False and denied["code"] == "APPROVAL_REQUIRED"
        outside = bridge.request("guard_check", {"tool_name": "write", "paths": ["unrelated/x.txt"]})
        assert outside["allowed"] is True and outside["reason"] == "OUTSIDE_GOVERNED_SCOPE"

        grant_write_approval(bridge)
        allowed = bridge.request("guard_check", {"tool_name": "edit", "paths": ["pilot/rtl/a.v"]})
        assert allowed["allowed"] is True and allowed["approval"] == "approval-1"

        bridge.request("dispatch", {"command": {"command_id": "revoke-1", "command_type": "REVOKE_APPROVAL", "actor": "user", "target_ref": {"object_id": "approval-1"}, "payload": {"reason": "user revoked"}}})
        denied_again = bridge.request("guard_check", {"tool_name": "write", "paths": ["pilot/rtl/b.v"]})
        assert denied_again["allowed"] is False and denied_again["code"] == "APPROVAL_REQUIRED"
    finally:
        bridge.stop()


def test_guard_bash_target_aware_copy_out_is_allowed(tmp_path):
    """cp FROM a governed scope TO a temp target must not require approval
    (regression for the source-path false positive)."""
    bridge = BridgeProcess(tmp_path / "state")
    try:
        create_started_task(bridge, scope_paths=("common/rtl/dev/qspi_flash",))
        decision = bridge.request("guard_check", {
            "tool_name": "bash",
            "command": "cp common/rtl/dev/qspi_flash/qspi_driver_new.v /tmp/dc-isolation/",
            "cwd": "/tmp/dc-isolation",
        })
        assert decision["allowed"] is True, decision
        # but writing INTO the scope via redirection with a neutral cwd is governed
        blocked = bridge.request("guard_check", {
            "tool_name": "bash",
            "command": "echo x > common/rtl/dev/qspi_flash/out.txt",
            "cwd": "/elsewhere",
        })
        assert blocked["allowed"] is False and blocked["code"] == "APPROVAL_REQUIRED", blocked
        # and cp INTO the scope is governed
        blocked_copy = bridge.request("guard_check", {
            "tool_name": "bash",
            "command": "cp /tmp/x.v common/rtl/dev/qspi_flash/",
            "cwd": "/tmp",
        })
        assert blocked_copy["allowed"] is False and blocked_copy["code"] == "APPROVAL_REQUIRED", blocked_copy
    finally:
        bridge.stop()


def test_guard_bash_classification(tmp_path):
    bridge = BridgeProcess(tmp_path / "state")
    try:
        create_started_task(bridge)
        read_only = bridge.request("guard_check", {"tool_name": "bash", "command": "cat pilot/rtl/a.v", "cwd": "pilot/rtl"})
        assert read_only["allowed"] is True and read_only["reason"] == "BASH_READ_ONLY"
        write_likely = bridge.request("guard_check", {"tool_name": "bash", "command": "sed -i 's/a/b/' a.v", "cwd": "pilot/rtl"})
        assert write_likely["allowed"] is False and write_likely["code"] == "APPROVAL_REQUIRED"
        outside = bridge.request("guard_check", {"tool_name": "bash", "command": "echo x > out.txt", "cwd": "elsewhere"})
        assert outside["allowed"] is True and outside["reason"] == "BASH_OUTSIDE_GOVERNED_SCOPE"
        grant_write_approval(bridge)
        allowed = bridge.request("guard_check", {"tool_name": "bash", "command": "python tool.py > result.log", "cwd": "pilot/rtl"})
        assert allowed["allowed"] is True and allowed["reason"] == "WRITE_APPROVAL_VALID"
    finally:
        bridge.stop()


def test_guard_protected_paths_always_denied(tmp_path):
    bridge = BridgeProcess(tmp_path / "state", config={"protected_paths": ["secret/dir"]})
    try:
        denied = bridge.request("guard_check", {"tool_name": "write", "paths": ["secret/dir/key.txt"]})
        assert denied["allowed"] is False and denied["code"] == "PROTECTED_PATH"
        free = bridge.request("guard_check", {"tool_name": "write", "paths": ["free/x.txt"]})
        assert free["allowed"] is True and free["reason"] == "NO_ACTIVE_TASK"
    finally:
        bridge.stop()


def test_guard_active_blocker_blocks_writes(tmp_path):
    bridge = BridgeProcess(tmp_path / "state")
    try:
        create_started_task(bridge)
        grant_write_approval(bridge)
        bridge.request("dispatch", {"command": {"command_id": "block-1", "command_type": "CREATE_BLOCKER", "actor": "verification-engineer", "target_ref": {"object_id": "task-m3"}, "payload": {"blocker_id": "blocker-1", "blocker_type": "EVIDENCE_CONFLICT", "description": "conflict", "required_action": "resolve", "resume_condition": "resolved"}}})
        denied = bridge.request("guard_check", {"tool_name": "edit", "paths": ["pilot/rtl/a.v"]})
        assert denied["allowed"] is False and denied["code"] == "BLOCKER_ACTIVE"
    finally:
        bridge.stop()


def test_role_output_validation_and_candidate_commands(tmp_path):
    bridge = BridgeProcess(tmp_path / "state")
    try:
        create_started_task(bridge)
        request = {"role": "verification-engineer", "task_ref": "task-m3", "scope": {"paths": ["pilot/rtl"]}, "approval_refs": [], "baseline_ref": "baseline-a", "expected_output": "evidence", "completion_criteria": "reproducible"}

        forbidden = bridge.request("invoke_role_result", {"request": request, "output": {"status": "PROPOSED", "gate_status": "SATISFIED"}}, expect_ok=False)
        assert forbidden["code"] == "ROLE_DIRECT_STATE_WRITE_FORBIDDEN"
        missing = bridge.request("invoke_role_result", {"request": {"role": "verification-engineer"}, "output": {}}, expect_ok=False)
        assert missing["code"] == "ROLE_REQUEST_INVALID"

        output = {"status": "PROPOSED", "evidence_candidates": [{"evidence_type": "simulation", "summary": "regression passed"}], "claim_candidates": [], "risk_proposals": [], "blocker_proposals": [], "artifact_candidates": [], "handoff_candidate": None, "summary": "done"}
        submitted = bridge.request("submit_candidates", {"request": request, "output": output, "actor": "verification-engineer"})
        types = [command["command_type"] for command in submitted["candidate_commands"]]
        assert types == ["REGISTER_EVIDENCE"]
        resubmitted = bridge.request("submit_candidates", {"request": request, "output": output, "actor": "verification-engineer"})
        assert [c["command_id"] for c in resubmitted["candidate_commands"]] == [c["command_id"] for c in submitted["candidate_commands"]]
    finally:
        bridge.stop()


def test_malformed_frames_do_not_kill_bridge(tmp_path):
    bridge = BridgeProcess(tmp_path / "state")
    try:
        error = bridge.raw("this is not json")
        assert error["ok"] is False and error["error"]["code"] == "BRIDGE_JSON_INVALID"
        error = bridge.raw(json.dumps({"id": "r9", "op": "frobnicate"}))
        assert error["ok"] is False and error["error"]["code"] == "BRIDGE_OP_UNKNOWN"
        assert bridge.request("hello")["service"] == "develoip-copilot-bridge"
    finally:
        bridge.stop()


def test_restart_restores_event_store_and_snapshot_conflict_detected(tmp_path):
    state_dir = tmp_path / "state"
    bridge = BridgeProcess(state_dir)
    try:
        create_started_task(bridge)
        bridge.request("save_snapshot")
        bridge.request("dispatch", {"command": {"command_id": "block-9", "command_type": "CREATE_BLOCKER", "actor": "orchestrator", "target_ref": {"object_id": "task-m3"}, "payload": {"blocker_id": "blocker-9", "description": "x"}}})
        stale = bridge.request("restore", expect_ok=False)
        assert stale["code"] == "SNAPSHOT_SEQUENCE_CONFLICT"
    finally:
        bridge.stop()

    revived = BridgeProcess(state_dir)
    try:
        status = revived.request("status")
        assert [task["object_id"] for task in status["tasks"]] == ["task-m3"]
        assert status["active_blockers"], "events after snapshot must survive restart via replay"
        revived.request("save_snapshot")
        restored = revived.request("restore")
        assert restored["restored"] is True and restored["last_sequence"] == status["last_sequence"]
        health = revived.request("health")
        assert health["ok"] is True
        workspace = revived.request("workspace_status")
        assert workspace["workspace_classification"] == "UNKNOWN"
    finally:
        revived.stop()
