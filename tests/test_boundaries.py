import json

import pytest

from adapters.omp_pi import OmpPiAdapter
from runtime.core import Runtime
from runtime.errors import ContractError
from runtime.roles import RoleInvocationLayer
from runtime.tools import ApprovalAdapter, BaselineCapture, EventStoreValidator, TestResultParser
from tests.test_runtime_core import command


def test_role_invocation_returns_structured_candidates_without_mutating_runtime():
    layer = RoleInvocationLayer()
    layer.register("system-investigator", lambda request: {"summary": "observed", "claim_candidates": [{"statement": "x"}]})

    response = layer.invoke({"role": "system-investigator", "task_ref": "task-1", "handoff_ref": None, "scope": {}, "approval_refs": [], "baseline_ref": "baseline-a", "allowed_tools": [], "expected_output": "claim", "completion_criteria": "observation"})

    assert response["role"] == "system-investigator"
    assert response["claim_candidates"] == [{"statement": "x"}]
    assert response["status"] == "PROPOSED"


def test_role_cannot_return_direct_derived_writes():
    layer = RoleInvocationLayer()
    layer.register("verification-engineer", lambda request: {"status": "SET_GATE_STATUS", "gate_status": "SATISFIED"})

    with pytest.raises(ContractError) as error:
        layer.invoke({"role": "verification-engineer", "task_ref": "task-1", "handoff_ref": None, "scope": {}, "approval_refs": [], "baseline_ref": "baseline-a", "allowed_tools": [], "expected_output": "evidence", "completion_criteria": "E3"})

    assert error.value.code == "ROLE_DIRECT_STATE_WRITE_FORBIDDEN"


def test_baseline_capture_is_deterministic_and_excludes_git(tmp_path):
    (tmp_path / "input.json").write_text('{"bytes": [18, 52]}', encoding="utf-8")
    capture = BaselineCapture().capture(tmp_path, configuration_set={"mode": "fixture"}, toolchain_versions={"python": "3.11"}, input_data_refs=["input.json"])

    assert capture["code_revision_or_workspace_snapshot"]
    assert capture["configuration_set"] == {"mode": "fixture"}
    assert capture["input_data_refs"] == ["input.json"]
    assert all(".git" not in entry["path"] for entry in capture["files"])


def test_event_store_validator_and_result_parser_use_structured_outputs(tmp_path):
    runtime = Runtime()
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "fixture"}))

    assert EventStoreValidator().validate(runtime.event_store)["valid"] is True
    parsed = TestResultParser().parse(json.dumps({"passed": True, "actual": 305419896, "expected": 305419896}))
    assert parsed == {"passed": True, "actual": 305419896, "expected": 305419896}


def test_omp_pi_adapter_maps_commands_to_runtime_without_second_state():
    runtime = Runtime()
    adapter = OmpPiAdapter(runtime)
    result = adapter.execute({"kind": "command", "command": command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "fixture"})})

    assert result["kind"] == "command_result"
    assert result["result"]["task"]["execution_status"] == "PROPOSED"
    with pytest.raises(ContractError) as error:
        adapter.execute({"kind": "command", "command": command("bad", "SET_PROJECT_STATUS", "orchestrator", "task-1", {"status": "CLOSED"})})
    assert error.value.code == "DERIVED_RESULT_WRITE_FORBIDDEN"


def test_approval_adapter_exposes_confirmation_without_bypassing_runtime():
    runtime = Runtime()
    runtime.dispatch(command("create", "CREATE_TASK", "orchestrator", payload={"task_id": "task-1", "goal": "approval"}))
    runtime.dispatch(command("classify", "CLASSIFY_TASK", "orchestrator", "task-1", {"task_kind": "IMPLEMENT", "primary_domain": "RTL", "domains": ["RTL"], "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE"], "required_capabilities": ["WRITE"], "execution_mode": "ORCHESTRATED", "scope": {"paths": ["fixture"]}}))
    runtime.dispatch(command("baseline", "BIND_BASELINE", "orchestrator", "task-1", {"baseline_id": "baseline-a", "code_revision_or_workspace_snapshot": "A", "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []}))
    adapter = ApprovalAdapter()
    adapter.request(runtime, command("request", "REQUEST_APPROVAL", "orchestrator", "task-1", {"approval_id": "approval-1", "requested_capability": "WRITE", "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE"], "requested_scope": {"paths": ["fixture"]}, "baseline_ref": "baseline-a"}))
    adapter.grant(runtime, command("grant", "GRANT_APPROVAL", "user", "approval-1", {"decision_basis": "fixture"}))
    assert runtime.query("approval-1", object_type="Approval")["status"] == "GRANTED"
