import pytest

from runtime.core import Runtime
from runtime.errors import ContractError


def command(command_id, command_type, actor, target="", payload=None, scope=None):
    return {
        "command_id": command_id,
        "command_type": command_type,
        "actor": actor,
        "target_ref": target,
        "scope": scope or {"paths": []},
        "payload": payload or {},
    }


def ready_task(runtime, task_id="task-1", baseline_id="baseline-a"):
    prefix = task_id
    runtime.dispatch(command(f"{prefix}-create", "CREATE_TASK", "orchestrator", payload={"task_id": task_id, "goal": "QSPI concat"}))
    runtime.dispatch(
        command(
            f"{prefix}-classify",
            "CLASSIFY_TASK",
            "orchestrator",
            task_id,
            {"task_kind": "INVESTIGATE", "primary_domain": "INTEGRATION", "domains": ["INTEGRATION"], "risk_factors": ["STORAGE_LAYOUT_CHANGE"], "required_capabilities": ["READ", "SAFE_EXECUTE"], "execution_mode": "ORCHESTRATED", "scope": {"paths": ["fixtures/qspi-concat"]}},
        )
    )
    runtime.dispatch(command(f"{prefix}-baseline", "BIND_BASELINE", "orchestrator", task_id, {"baseline_id": baseline_id, "code_revision_or_workspace_snapshot": "A", "configuration_set": {}, "toolchain_versions": {"python": "3.11"}, "input_data_refs": ["input-a"], "dependency_refs": []}))


def test_S02_task_can_be_classified_and_bound_to_baseline():
    runtime = Runtime()
    ready_task(runtime)
    assert runtime.query("task-1")["execution_status"] == "READY"
    assert runtime.query("task-1")["baseline_ref"] == "baseline-a"


def test_S04_read_task_can_be_created_classified_bound_and_started():
    runtime = Runtime()
    ready_task(runtime)

    result = runtime.dispatch(command("start", "START_TASK", "orchestrator", "task-1"))

    assert result["task"]["execution_status"] == "RUNNING"
    assert runtime.query("task-1")["closure_status"] == "OPEN"


def test_S03_direct_derived_result_write_is_rejected():
    runtime = Runtime()
    ready_task(runtime)

    with pytest.raises(ContractError) as error:
        runtime.dispatch(command("bad", "SET_GATE_STATUS", "orchestrator", "task-1", {"status": "SATISFIED"}))

    assert error.value.code == "DERIVED_RESULT_WRITE_FORBIDDEN"


def test_S05_non_orchestrator_cannot_activate_classification():
    runtime = Runtime()
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "QSPI"}))

    with pytest.raises(ContractError) as error:
        runtime.dispatch(command("classify", "CLASSIFY_TASK", "system-investigator", "task-1", {"task_kind": "INVESTIGATE"}))

    assert error.value.code == "OWNERSHIP_VIOLATION"


def test_start_write_risk_waits_for_approval_before_start():
    runtime = Runtime()
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "fix"}))
    runtime.dispatch(command("classify", "CLASSIFY_TASK", "orchestrator", "task-1", {"task_kind": "IMPLEMENT", "primary_domain": "RTL", "domains": ["RTL"], "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE"], "required_capabilities": ["WRITE"], "execution_mode": "ORCHESTRATED", "scope": {"paths": ["fixtures/qspi-concat/rtl"]}}))
    runtime.dispatch(command("baseline", "BIND_BASELINE", "orchestrator", "task-1", {"baseline_id": "baseline-a", "code_revision_or_workspace_snapshot": "A", "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []}))

    result = runtime.dispatch(command("start", "START_TASK", "orchestrator", "task-1"))

    assert result["event"]["event_type"] == "TASK_AWAITING_APPROVAL"
    assert runtime.query("task-1")["execution_status"] == "AWAITING_APPROVAL"


def test_approval_can_be_granted_and_revoked():
    runtime = Runtime()
    ready_task(runtime)
    runtime.dispatch(command("request", "REQUEST_APPROVAL", "orchestrator", "task-1", {"approval_id": "approval-1", "requested_capability": "WRITE", "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE"], "requested_scope": {"paths": ["fixtures/qspi-concat/rtl"]}, "baseline_ref": "baseline-a"}))
    runtime.dispatch(command("grant", "GRANT_APPROVAL", "user", "approval-1", {"decision_basis": "fixture change"}))
    assert runtime.query("approval-1", object_type="Approval")["status"] == "GRANTED"
    runtime.dispatch(command("revoke", "REVOKE_APPROVAL", "user", "approval-1", {"reason": "stop"}))
    assert runtime.query("approval-1", object_type="Approval")["status"] == "REVOKED"


def test_S09_artifact_evidence_and_claim_are_linked_without_direct_support_write():
    runtime = Runtime()
    ready_task(runtime)
    runtime.dispatch(command("start", "START_TASK", "orchestrator", "task-1"))
    runtime.dispatch(command("artifact", "REGISTER_ARTIFACT", "system-investigator", "task-1", {"artifact_id": "artifact-1", "artifact_type": "observation", "location": "fixtures/qspi-concat/input.json", "baseline_ref": "baseline-a", "scope": {"paths": ["fixtures/qspi-concat/input.json"]}}))
    runtime.dispatch(command("evidence", "REGISTER_EVIDENCE", "system-investigator", "task-1", {"evidence_id": "evidence-1", "evidence_type": "observation", "artifact_refs": ["artifact-1"], "baseline_ref": "baseline-a", "summary": "input differs", "reproducibility_level": "E2", "relevance": "direct", "coverage": "input", "independence": ["SELF_PRODUCED"]}))
    runtime.dispatch(command("claim", "CREATE_CLAIM", "system-investigator", "task-1", {"claim_id": "claim-1", "statement": "concat is wrong", "claim_type": "OBSERVATION", "baseline_ref": "baseline-a"}))
    runtime.dispatch(command("link", "LINK_CLAIM_EVIDENCE", "system-investigator", "claim-1", {"evidence_ref": "evidence-1", "relation": "supports"}))

    claim = runtime.query("claim-1", object_type="Claim")
    assert claim["status"] == "SUPPORTED"


def test_C03_S14_handoff_acceptance_does_not_accept_claim():
    runtime = Runtime()
    ready_task(runtime)
    runtime.dispatch(command("handoff", "SUBMIT_HANDOFF", "system-investigator", "task-1", {"handoff_id": "handoff-1", "target_role": "verification-engineer", "baseline_ref": "baseline-a", "context_package": {"MUST_HAVE": ["input"], "USEFUL": [], "EXCLUDED": []}, "expected_output": "reproduction", "completion_criteria": "E3"}))
    runtime.dispatch(command("accept-handoff", "ACCEPT_HANDOFF", "verification-engineer", "handoff-1", {"acceptance_scope": "input usable", "acceptance_basis": "MUST_HAVE complete", "baseline_ref": "baseline-a"}))

    assert runtime.query("handoff-1", object_type="Handoff")["acceptance_status"] == "ACCEPTED"
    assert runtime.query("task-1")["acceptance_summary"]["technical_acceptance"] == "NOT_REVIEWED"
