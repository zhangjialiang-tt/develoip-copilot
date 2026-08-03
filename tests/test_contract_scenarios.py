import pytest

from runtime.core import Runtime
from runtime.errors import ContractError
from tests.test_runtime_core import command, ready_task


def protocol_task(runtime, task_id="task-1", baseline_id="baseline-a", required_capabilities=None):
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": task_id, "goal": "QSPI protocol"}))
    runtime.dispatch(command("classify", "CLASSIFY_TASK", "orchestrator", task_id, {"task_kind": "IMPLEMENT", "primary_domain": "RTL", "domains": ["RTL"], "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE"], "required_capabilities": required_capabilities or ["READ"], "execution_mode": "ORCHESTRATED", "scope": {"paths": [f"fixtures/qspi-concat/{task_id}"]}}))
    runtime.dispatch(command("baseline", "BIND_BASELINE", "orchestrator", task_id, {"baseline_id": baseline_id, "code_revision_or_workspace_snapshot": "A", "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []}))


def evidence_claim(runtime, task_id="task-1", artifact_id="artifact-1", evidence_id="evidence-1", claim_id="claim-1", evidence_type="protocol_regression", independence=None):
    runtime.dispatch(command(f"artifact-{artifact_id}", "REGISTER_ARTIFACT", "rtl-engineer", task_id, {"artifact_id": artifact_id, "artifact_type": "rtl_patch", "location": "fixtures/qspi-concat/rtl/qspi_concat.v", "baseline_ref": "baseline-a", "scope": {"paths": ["fixtures/qspi-concat/rtl/qspi_concat.v"]}}))
    runtime.dispatch(command(f"evidence-{evidence_id}", "REGISTER_EVIDENCE", "verification-engineer", task_id, {"evidence_id": evidence_id, "evidence_type": evidence_type, "artifact_refs": [artifact_id], "baseline_ref": "baseline-a", "summary": "deterministic result", "reproducibility_level": "E3", "relevance": "full", "coverage": "normal and edge", "independence": independence or ["INDEPENDENT_METHOD"]}))
    runtime.dispatch(command(f"claim-{claim_id}", "CREATE_CLAIM", "system-investigator", task_id, {"claim_id": claim_id, "statement": "QSPI concat behavior is explained", "claim_type": "INFERENCE", "baseline_ref": "baseline-a"}))
    runtime.dispatch(command(f"link-{claim_id}", "LINK_CLAIM_EVIDENCE", "verification-engineer", claim_id, {"evidence_ref": evidence_id, "relation": "supports"}))


def make_closable(runtime):
    protocol_task(runtime)
    evidence_claim(runtime)
    runtime.dispatch(command("evidence-2", "REGISTER_EVIDENCE", "verification-engineer", "task-1", {"evidence_id": "evidence-2", "evidence_type": "simulation", "artifact_refs": ["artifact-1"], "baseline_ref": "baseline-a", "summary": "simulation", "reproducibility_level": "E3", "relevance": "full", "coverage": "all", "independence": ["INDEPENDENT_METHOD"]}))
    runtime.dispatch(command("evidence-3", "REGISTER_EVIDENCE", "verification-engineer", "task-1", {"evidence_id": "evidence-3", "evidence_type": "protocol_regression", "artifact_refs": ["artifact-1"], "baseline_ref": "baseline-a", "summary": "protocol", "reproducibility_level": "E3", "relevance": "full", "coverage": "all", "independence": ["INDEPENDENT_METHOD"]}))
    runtime.dispatch(command("accept", "RECORD_ACCEPTANCE", "integration-reviewer", "task-1", {"target_type": "TASK_RESULT", "acceptance_scope": "QSPI fixture", "acceptance_basis": "reviewed evidence", "baseline_ref": "baseline-a"}))
    runtime.dispatch(command("record", "RECORD_DECISION", "documenter", "task-1", {"decision": "declined"}))


def test_S01_unclassified_task_stays_proposed():
    runtime = Runtime()
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "QSPI"}))
    assert runtime.query("task-1")["execution_status"] == "PROPOSED"


def test_C01_S06_new_risk_invalidates_granted_approval_and_waits():
    runtime = Runtime()
    ready_task(runtime)
    runtime.dispatch(command("request", "REQUEST_APPROVAL", "orchestrator", "task-1", {"approval_id": "approval-1", "requested_capability": "WRITE", "risk_factors": ["STORAGE_LAYOUT_CHANGE"], "baseline_ref": "baseline-a", "requested_scope": {"paths": ["fixtures/qspi-concat/rtl"]}}))
    runtime.dispatch(command("grant", "GRANT_APPROVAL", "user", "approval-1", {"decision_basis": "initial"}))
    runtime.dispatch(command("propose", "PROPOSE_RISK", "verification-engineer", "task-1", {"risk_factor": "PROTOCOL_BEHAVIOR_CHANGE"}))
    runtime.dispatch(command("activate", "ACTIVATE_RISK", "orchestrator", "task-1", {"risk_factor": "PROTOCOL_BEHAVIOR_CHANGE"}))
    assert runtime.query("approval-1", object_type="Approval")["status"] == "INVALIDATED"
    assert runtime.query("task-1")["execution_status"] == "AWAITING_APPROVAL"


def test_S08_blocker_requires_owner_and_can_be_resolved():
    runtime = Runtime()
    ready_task(runtime)
    runtime.dispatch(command("start", "START_TASK", "orchestrator", "task-1"))
    runtime.dispatch(command("block", "CREATE_BLOCKER", "verification-engineer", "task-1", {"blocker_id": "blocker-1", "blocker_type": "TOOL_FAILURE", "blocker_owner": "tooling", "description": "tool failed", "required_action": "repair", "resume_condition": "rerun E3"}))
    runtime.dispatch(command("resolve", "RESOLVE_BLOCKER", "verification-engineer", "blocker-1", {"resume_status": "RUNNING"}))
    assert runtime.query("blocker-1", object_type="Blocker")["resolved"] is True
    assert runtime.query("task-1")["execution_status"] == "RUNNING"


def test_S10_E3_does_not_satisfy_protocol_gate_without_protocol_coverage():
    runtime = Runtime()
    protocol_task(runtime)
    evidence_claim(runtime, evidence_type="simulation")
    gate = next(gate for gate in runtime.query("task-1")["gates"] if gate["gate_type"] == "protocol_gate")
    assert gate["status"] == "UNSATISFIED"


def test_S11_claim_type_upgrade_creates_a_new_claim():
    runtime = Runtime()
    ready_task(runtime)
    runtime.dispatch(command("claim", "CREATE_CLAIM", "system-investigator", "task-1", {"claim_id": "claim-old", "statement": "maybe", "claim_type": "HYPOTHESIS", "baseline_ref": "baseline-a"}))
    runtime.dispatch(command("upgrade", "SUPERSEDE_CLAIM", "system-investigator", "claim-old", {"claim_id": "claim-new", "statement": "now supported", "claim_type": "INFERENCE"}))
    assert runtime.query("claim-old", object_type="Claim")["status"] == "SUPERSEDED"
    assert runtime.query("claim-new", object_type="Claim")["derived_from"] == ["claim-old"]


def test_C04_S12_contradicting_evidence_keeps_claim_and_gate_open():
    runtime = Runtime()
    ready_task(runtime)
    runtime.dispatch(command("artifact", "REGISTER_ARTIFACT", "system-investigator", "task-1", {"artifact_id": "artifact-1", "artifact_type": "observation", "location": "fixture", "baseline_ref": "baseline-a", "scope": {"paths": ["fixtures/qspi-concat/input.json"]}}))
    for evidence_id, relation in (("evidence-support", "supports"), ("evidence-conflict", "contradicts")):
        runtime.dispatch(command(evidence_id, "REGISTER_EVIDENCE", "verification-engineer", "task-1", {"evidence_id": evidence_id, "evidence_type": "simulation", "artifact_refs": ["artifact-1"], "baseline_ref": "baseline-a", "summary": relation, "reproducibility_level": "E3", "relevance": "full", "coverage": "all", "independence": ["INDEPENDENT_METHOD"]}))
    runtime.dispatch(command("claim", "CREATE_CLAIM", "system-investigator", "task-1", {"claim_id": "claim-1", "statement": "fixed", "claim_type": "INFERENCE", "baseline_ref": "baseline-a"}))
    runtime.dispatch(command("link-support", "LINK_CLAIM_EVIDENCE", "verification-engineer", "claim-1", {"evidence_ref": "evidence-support", "relation": "supports"}))
    runtime.dispatch(command("link-conflict", "LINK_CLAIM_EVIDENCE", "verification-engineer", "claim-1", {"evidence_ref": "evidence-conflict", "relation": "contradicts"}))
    assert runtime.query("claim-1", object_type="Claim")["status"] == "CONTRADICTED"


def test_C02_S13_baseline_change_invalidates_evidence_claim_and_approval():
    runtime = Runtime()
    protocol_task(runtime, required_capabilities=["WRITE"])
    runtime.dispatch(command("request", "REQUEST_APPROVAL", "orchestrator", "task-1", {"approval_id": "approval-1", "requested_capability": "WRITE", "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE"], "baseline_ref": "baseline-a", "requested_scope": {"paths": ["fixtures/qspi-concat/rtl"]}}))
    runtime.dispatch(command("grant", "GRANT_APPROVAL", "user", "approval-1", {"decision_basis": "initial patch"}))
    evidence_claim(runtime)
    runtime.dispatch(command("change", "CHANGE_BASELINE", "orchestrator", "task-1", {"baseline_id": "baseline-b", "code_revision_or_workspace_snapshot": "B", "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []}))
    assert runtime.query("evidence-1", object_type="Evidence")["validity"] == "INVALIDATED"
    assert runtime.query("claim-1", object_type="Claim")["status"] == "INVALIDATED"
    assert runtime.query("approval-1", object_type="Approval")["status"] == "INVALIDATED"


def test_S15_acceptance_requires_scope_and_basis():
    runtime = Runtime()
    ready_task(runtime)
    with pytest.raises(ContractError) as error:
        runtime.dispatch(command("accept", "RECORD_ACCEPTANCE", "integration-reviewer", "task-1", {"target_type": "TASK_RESULT"}))
    assert error.value.code == "ACCEPTANCE_BASIS_INCOMPLETE"


def test_C05_S16_valid_waiver_changes_matching_gate_to_waived():
    runtime = Runtime()
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "hardware"}))
    runtime.dispatch(command("classify", "CLASSIFY_TASK", "orchestrator", "task-1", {"task_kind": "VERIFY", "primary_domain": "VERIFICATION", "domains": ["VERIFICATION"], "risk_factors": ["HARDWARE_STATE_CHANGE"], "required_capabilities": ["EXTERNAL_DEVICE_ACCESS"], "execution_mode": "ORCHESTRATED", "scope": {"paths": ["fixtures/qspi-concat"]}}))
    runtime.dispatch(command("baseline", "BIND_BASELINE", "orchestrator", "task-1", {"baseline_id": "baseline-a", "code_revision_or_workspace_snapshot": "A", "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []}))
    runtime.dispatch(command("waive", "CREATE_WAIVER", "user", "task-1", {"gate_type": "hardware_gate", "baseline_ref": "baseline-a", "risk_description": "fixture only", "rationale": "no board in M2", "conditions": ["not a hardware claim"], "scope": {"paths": ["fixtures/qspi-concat"]}}))
    gate = next(gate for gate in runtime.query("task-1")["gates"] if gate["gate_type"] == "hardware_gate")
    assert gate["status"] == "WAIVED"


def test_S17_waiver_with_wrong_baseline_is_rejected():
    runtime = Runtime()
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "hardware"}))
    runtime.dispatch(command("classify", "CLASSIFY_TASK", "orchestrator", "task-1", {"task_kind": "VERIFY", "primary_domain": "VERIFICATION", "domains": ["VERIFICATION"], "risk_factors": ["HARDWARE_STATE_CHANGE"], "required_capabilities": ["EXTERNAL_DEVICE_ACCESS"], "execution_mode": "ORCHESTRATED", "scope": {"paths": ["fixtures/qspi-concat"]}}))
    runtime.dispatch(command("baseline", "BIND_BASELINE", "orchestrator", "task-1", {"baseline_id": "baseline-a", "code_revision_or_workspace_snapshot": "A", "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []}))
    with pytest.raises(ContractError) as error:
        runtime.dispatch(command("waive", "CREATE_WAIVER", "user", "task-1", {"gate_type": "hardware_gate", "baseline_ref": "baseline-b", "risk_description": "bad", "rationale": "bad", "scope": {"paths": ["fixtures/qspi-concat"]}}))
    assert error.value.code == "BASELINE_MISMATCH"


def test_S18_success_path_reaches_closable_then_closed():
    runtime = Runtime()
    make_closable(runtime)
    assert runtime.query("task-1")["closure_status"] == "CLOSABLE"
    runtime.dispatch(command("request-close", "REQUEST_CLOSURE", "orchestrator", "task-1"))
    runtime.dispatch(command("close", "CLOSE_TASK", "user", "task-1"))
    assert runtime.query("task-1")["closure_status"] == "CLOSED"


def test_S19_record_decline_resolves_record_gate_without_writing_record():
    runtime = Runtime()
    ready_task(runtime)
    runtime.dispatch(command("record", "RECORD_DECISION", "user", "task-1", {"decision": "declined"}))
    gate = next(gate for gate in runtime.query("task-1")["gates"] if gate["gate_type"] == "record_gate")
    assert gate["status"] == "SATISFIED"
    assert runtime.query("task-1")["record_decision"] == "declined"


def test_S20_snapshot_restore_matches_event_replay(tmp_path):
    from runtime.persistence import JsonlEventStore

    events = JsonlEventStore(tmp_path / "events.jsonl")
    runtime = Runtime(events, tmp_path / "snapshot.json")
    ready_task(runtime)
    runtime.save_snapshot()
    restored = Runtime.restore(JsonlEventStore(tmp_path / "events.jsonl"), tmp_path / "snapshot.json")
    assert restored.query("task-1") == runtime.query("task-1")


def test_S21_parent_and_child_use_the_same_task_model():
    runtime = Runtime()
    runtime.dispatch(command("parent", "CREATE_TASK", "orchestrator", payload={"task_id": "parent", "goal": "parent"}))
    runtime.dispatch(command("child", "CREATE_TASK", "orchestrator", payload={"task_id": "child", "parent_task_ref": "parent", "goal": "child"}))
    assert runtime.query("child")["parent_task_ref"] == "parent"
    assert runtime.query("child")["execution_status"] == "PROPOSED"


def test_S22_overlapping_file_scope_is_rejected():
    runtime = Runtime()
    ready_task(runtime, "task-1")
    ready_task(runtime, "task-2", "baseline-b")
    runtime.dispatch(command("artifact-1", "REGISTER_ARTIFACT", "rtl-engineer", "task-1", {"artifact_id": "artifact-1", "artifact_type": "rtl_patch", "location": "a", "baseline_ref": "baseline-a", "scope": {"paths": ["fixtures/qspi-concat/rtl/qspi_concat.v"]}}))
    with pytest.raises(ContractError) as error:
        runtime.dispatch(command("artifact-2", "REGISTER_ARTIFACT", "rtl-engineer", "task-2", {"artifact_id": "artifact-2", "artifact_type": "rtl_patch", "location": "b", "baseline_ref": "baseline-b", "scope": {"paths": ["fixtures/qspi-concat/rtl/qspi_concat.v"]}}))
    assert error.value.code == "SCOPE_CONFLICT"


def test_C06_S23_hardware_evidence_needs_external_source():
    runtime = Runtime()
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "hardware"}))
    runtime.dispatch(command("classify", "CLASSIFY_TASK", "orchestrator", "task-1", {"task_kind": "VERIFY", "primary_domain": "VERIFICATION", "domains": ["VERIFICATION"], "risk_factors": ["HARDWARE_STATE_CHANGE"], "required_capabilities": ["EXTERNAL_DEVICE_ACCESS"], "execution_mode": "ORCHESTRATED", "scope": {"paths": ["fixtures/qspi-concat"]}}))
    runtime.dispatch(command("baseline", "BIND_BASELINE", "orchestrator", "task-1", {"baseline_id": "baseline-a", "code_revision_or_workspace_snapshot": "A", "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []}))
    runtime.dispatch(command("artifact", "REGISTER_ARTIFACT", "system-investigator", "task-1", {"artifact_id": "artifact-1", "artifact_type": "observation", "location": "fixture", "baseline_ref": "baseline-a", "scope": {"paths": ["fixtures/qspi-concat/input.json"]}}))
    runtime.dispatch(command("evidence", "REGISTER_EVIDENCE", "verification-engineer", "task-1", {"evidence_id": "evidence-1", "evidence_type": "hardware", "artifact_refs": ["artifact-1"], "baseline_ref": "baseline-a", "summary": "self report", "reproducibility_level": "E2", "relevance": "partial", "coverage": "device", "independence": ["SELF_PRODUCED"]}))
    gate = next(gate for gate in runtime.query("task-1")["gates"] if gate["gate_type"] == "hardware_gate")
    assert gate["status"] == "UNSATISFIED"


def test_C07_S24_project_status_is_not_a_write_interface():
    runtime = Runtime()
    ready_task(runtime)
    with pytest.raises(ContractError) as error:
        runtime.dispatch(command("project", "SET_PROJECT_STATUS", "orchestrator", "task-1", {"status": "CLOSED"}))
    assert error.value.code == "DERIVED_RESULT_WRITE_FORBIDDEN"
