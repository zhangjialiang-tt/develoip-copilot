import pytest

from adapters.omp_pi import OmpPiAdapter
from runtime.core import Runtime
from runtime.errors import ContractError
from tests.test_runtime_core import command


def via(adapter, command_id, command_type, actor="orchestrator", target="", payload=None):
    return adapter.execute({"kind": "command", "command": command(command_id, command_type, actor, target, payload)})


def setup_adapter_task(adapter, task_id="task-1", baseline_id="baseline-a", capabilities=None):
    via(adapter, f"{task_id}-create", "CREATE_TASK", payload={"task_id": task_id, "goal": "adapter"})
    via(adapter, f"{task_id}-classify", "CLASSIFY_TASK", target=task_id, payload={"task_kind": "IMPLEMENT", "primary_domain": "RTL", "domains": ["RTL"], "risk_factors": ["PROTOCOL_BEHAVIOR_CHANGE"], "required_capabilities": capabilities or ["READ"], "execution_mode": "ORCHESTRATED", "scope": {"paths": ["fixtures/qspi-concat"]}})
    via(adapter, f"{task_id}-baseline", "BIND_BASELINE", target=task_id, payload={"baseline_id": baseline_id, "code_revision_or_workspace_snapshot": baseline_id, "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []})


def test_omp_pi_adapter_regression_covers_S03_S06_S13_S20_S24():
    runtime = Runtime()
    adapter = OmpPiAdapter(runtime)
    setup_adapter_task(adapter, capabilities=["WRITE"])

    with pytest.raises(ContractError) as s03:
        via(adapter, "s03", "SET_GATE_STATUS", target="task-1", payload={"status": "SATISFIED"})
    assert s03.value.code == "DERIVED_RESULT_WRITE_FORBIDDEN"

    s06 = via(adapter, "s06", "START_TASK", target="task-1")
    assert s06["result"]["task"]["execution_status"] == "AWAITING_APPROVAL"

    s13 = via(adapter, "s13", "CHANGE_BASELINE", target="task-1", payload={"baseline_id": "baseline-b", "code_revision_or_workspace_snapshot": "B", "configuration_set": {}, "toolchain_versions": {}, "input_data_refs": [], "dependency_refs": []})
    assert s13["result"]["task"]["baseline_ref"] == "baseline-b"

    s20 = adapter.execute({"kind": "restore"})
    assert s20["kind"] == "restore_result"

    with pytest.raises(ContractError) as s24:
        via(adapter, "s24", "SET_PROJECT_STATUS", target="task-1", payload={"status": "CLOSED"})
    assert s24.value.code == "DERIVED_RESULT_WRITE_FORBIDDEN"
