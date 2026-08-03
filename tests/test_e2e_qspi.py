import pytest

from runtime.core import Runtime
from runtime.errors import ContractError
from tests.test_runtime_core import command


def setup_qspi_task(runtime: Runtime) -> None:
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "qspi-task", "goal": "QSPI concat anomaly"}))
    runtime.dispatch(command("classify", "CLASSIFY_TASK", "orchestrator", "qspi-task", {"task_kind": "INVESTIGATE", "primary_domain": "INTEGRATION", "domains": ["RTL", "VERIFICATION", "INTEGRATION"], "risk_factors": ["STORAGE_LAYOUT_CHANGE"], "required_capabilities": ["READ", "SAFE_EXECUTE"], "execution_mode": "ORCHESTRATED", "scope": {"paths": ["fixtures/qspi-concat"]}}))
    runtime.dispatch(command("baseline-a", "BIND_BASELINE", "orchestrator", "qspi-task", {"baseline_id": "baseline-a", "code_revision_or_workspace_snapshot": "fixture-A", "configuration_set": {"baseline": "A"}, "toolchain_versions": {"python": "3.11"}, "input_data_refs": ["fixtures/qspi-concat/input.json"], "dependency_refs": []}))
    runtime.dispatch(command("start", "START_TASK", "orchestrator", "qspi-task"))


def register_observation(runtime: Runtime) -> None:
    runtime.dispatch(command("obs-artifact", "REGISTER_ARTIFACT", "system-investigator", "qspi-task", {"artifact_id": "observation-a", "artifact_type": "observation", "location": "fixtures/qspi-concat/input.json", "baseline_ref": "baseline-a", "scope": {"paths": ["fixtures/qspi-concat/input.json"]}}))
    runtime.dispatch(command("obs-evidence", "REGISTER_EVIDENCE", "system-investigator", "qspi-task", {"evidence_id": "observation-evidence", "evidence_type": "observation", "artifact_refs": ["observation-a"], "baseline_ref": "baseline-a", "summary": "bus bytes are correct", "reproducibility_level": "E2", "relevance": "direct", "coverage": "input", "independence": ["EXTERNAL_SOURCE"]}))
    runtime.dispatch(command("obs-claim", "CREATE_CLAIM", "system-investigator", "qspi-task", {"claim_id": "observation-claim", "statement": "input bytes are correct but concat is wrong", "claim_type": "OBSERVATION", "baseline_ref": "baseline-a"}))
    runtime.dispatch(command("obs-link", "LINK_CLAIM_EVIDENCE", "system-investigator", "observation-claim", {"evidence_ref": "observation-evidence", "relation": "supports"}))


def authorize_protocol_write(runtime: Runtime) -> None:
    runtime.dispatch(command("propose-risk", "PROPOSE_RISK", "verification-engineer", "qspi-task", {"risk_factor": "PROTOCOL_BEHAVIOR_CHANGE"}))
    runtime.dispatch(command("activate-risk", "ACTIVATE_RISK", "orchestrator", "qspi-task", {"risk_factor": "PROTOCOL_BEHAVIOR_CHANGE"}))
    runtime.dispatch(command("request-write", "REQUEST_APPROVAL", "orchestrator", "qspi-task", {"approval_id": "write-a", "requested_capability": "WRITE", "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE"], "requested_scope": {"paths": ["fixtures/qspi-concat/rtl/qspi_concat.v"]}, "baseline_ref": "baseline-a"}))
    runtime.dispatch(command("grant-write", "GRANT_APPROVAL", "user", "write-a", {"decision_basis": "authorized fixture patch"}))
    runtime.dispatch(command("resume", "START_TASK", "orchestrator", "qspi-task"))


def register_fixed_result(runtime: Runtime, *, contradiction: bool = False) -> None:
    runtime.dispatch(command("baseline-b", "CHANGE_BASELINE", "orchestrator", "qspi-task", {"baseline_id": "baseline-b", "code_revision_or_workspace_snapshot": "fixture-B", "configuration_set": {"baseline": "B"}, "toolchain_versions": {"python": "3.11"}, "input_data_refs": ["fixtures/qspi-concat/input.json"], "dependency_refs": []}))
    runtime.dispatch(command("request-write-b", "REQUEST_APPROVAL", "orchestrator", "qspi-task", {"approval_id": "write-b", "requested_capability": "WRITE", "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE", "BASELINE_CHANGE"], "requested_scope": {"paths": ["fixtures/qspi-concat/rtl/qspi_concat.v"]}, "baseline_ref": "baseline-b"}))
    runtime.dispatch(command("grant-write-b", "GRANT_APPROVAL", "user", "write-b", {"decision_basis": "authorized Baseline B patch"}))
    runtime.dispatch(command("resume-b", "START_TASK", "orchestrator", "qspi-task"))
    runtime.dispatch(command("fix-artifact", "REGISTER_ARTIFACT", "rtl-engineer", "qspi-task", {"artifact_id": "fix-artifact", "artifact_type": "rtl_patch", "location": "fixtures/qspi-concat/rtl/qspi_concat.v", "baseline_ref": "baseline-b", "scope": {"paths": ["fixtures/qspi-concat/rtl/qspi_concat.v"]}}))
    runtime.dispatch(command("fixed-claim", "CREATE_CLAIM", "system-investigator", "qspi-task", {"claim_id": "fixed-claim", "statement": "Baseline B fixes QSPI concatenation", "claim_type": "INFERENCE", "baseline_ref": "baseline-b"}))
    runtime.dispatch(command("fixed-sim", "REGISTER_EVIDENCE", "verification-engineer", "qspi-task", {"evidence_id": "fixed-sim", "evidence_type": "simulation", "artifact_refs": ["fix-artifact"], "baseline_ref": "baseline-b", "summary": "B passes RTL fixture", "reproducibility_level": "E3", "relevance": "full", "coverage": "normal and edge", "independence": ["INDEPENDENT_METHOD"]}))
    runtime.dispatch(command("fixed-protocol", "REGISTER_EVIDENCE", "verification-engineer", "qspi-task", {"evidence_id": "fixed-protocol", "evidence_type": "protocol_regression", "artifact_refs": ["fix-artifact"], "baseline_ref": "baseline-b", "summary": "B passes protocol regression", "reproducibility_level": "E3", "relevance": "full", "coverage": "normal, edge, order", "independence": ["INDEPENDENT_ROLE", "INDEPENDENT_METHOD"]}))
    runtime.dispatch(command("fixed-link", "LINK_CLAIM_EVIDENCE", "verification-engineer", "fixed-claim", {"evidence_ref": "fixed-protocol", "relation": "contradicts" if contradiction else "supports"}))


def test_qspi_success_path_closes_only_after_review_and_record_gate():
    runtime = Runtime()
    setup_qspi_task(runtime)
    register_observation(runtime)
    authorize_protocol_write(runtime)
    register_fixed_result(runtime)
    runtime.dispatch(command("handoff", "SUBMIT_HANDOFF", "rtl-engineer", "qspi-task", {"handoff_id": "verification-handoff", "target_role": "verification-engineer", "baseline_ref": "baseline-b", "authorization_refs": ["write-a"], "artifact_refs": ["fix-artifact"], "expected_output": "independent verification", "completion_criteria": "E3 protocol regression", "context_package": {"MUST_HAVE": ["fix-artifact"], "USEFUL": [], "EXCLUDED": []}}))
    runtime.dispatch(command("handoff-accept", "ACCEPT_HANDOFF", "verification-engineer", "verification-handoff", {"acceptance_scope": "verification input", "acceptance_basis": "artifact and baseline present", "baseline_ref": "baseline-b"}))
    runtime.dispatch(command("accept-result", "RECORD_ACCEPTANCE", "integration-reviewer", "qspi-task", {"target_type": "TASK_RESULT", "acceptance_scope": "QSPI fixture Baseline B", "acceptance_basis": "independent E3 evidence and scope review", "baseline_ref": "baseline-b"}))
    runtime.dispatch(command("record", "RECORD_DECISION", "documenter", "qspi-task", {"decision": "written"}))

    assert runtime.query("qspi-task")["closure_status"] == "CLOSABLE"
    runtime.dispatch(command("request-close", "REQUEST_CLOSURE", "orchestrator", "qspi-task"))
    runtime.dispatch(command("close", "CLOSE_TASK", "user", "qspi-task"))
    assert runtime.query("qspi-task")["closure_status"] == "CLOSED"
    assert runtime.query("observation-evidence", object_type="Evidence")["validity"] == "INVALIDATED"


def test_qspi_verification_failure_creates_rework_path():
    runtime = Runtime()
    setup_qspi_task(runtime)
    register_observation(runtime)
    authorize_protocol_write(runtime)
    register_fixed_result(runtime, contradiction=True)

    assert runtime.query("fixed-claim", object_type="Claim")["status"] == "CONTRADICTED"
    assert runtime.query("qspi-task")["closure_status"] == "OPEN"
    runtime.dispatch(command("rework", "REQUEST_REWORK", "integration-reviewer", "qspi-task"))
    assert runtime.query("qspi-task")["execution_status"] == "REWORK_REQUIRED"


def test_C08_S07_qspi_revoked_write_approval_marks_artifact_for_review_and_blocks_new_write():
    runtime = Runtime()
    setup_qspi_task(runtime)
    authorize_protocol_write(runtime)
    runtime.dispatch(command("artifact", "REGISTER_ARTIFACT", "rtl-engineer", "qspi-task", {"artifact_id": "pending-artifact", "artifact_type": "rtl_patch", "location": "fixtures/qspi-concat/rtl/qspi_concat.v", "baseline_ref": "baseline-a", "scope": {"paths": ["fixtures/qspi-concat/rtl/qspi_concat.v"]}}))
    runtime.dispatch(command("revoke", "REVOKE_APPROVAL", "user", "write-a", {"reason": "scope review"}))
    assert runtime.query("pending-artifact", object_type="Artifact")["review_required"] is True
    assert runtime.query("qspi-task")["execution_status"] == "AWAITING_APPROVAL"
    with pytest.raises(ContractError):
        runtime.dispatch(command("new-artifact", "REGISTER_ARTIFACT", "rtl-engineer", "qspi-task", {"artifact_id": "new-artifact", "artifact_type": "rtl_patch", "location": "fixtures/qspi-concat/rtl/qspi_concat.v", "baseline_ref": "baseline-a", "scope": {"paths": ["fixtures/qspi-concat/rtl/qspi_concat.v"]}}))
