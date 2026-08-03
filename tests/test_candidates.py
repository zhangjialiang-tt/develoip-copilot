import json

from runtime.candidates import build_candidate_commands


def task(task_id="task-1"):
    return {"object_id": task_id, "object_type": "Task", "scope": {"paths": ["rtl/qspi"]}}


VALIDATED = {
    "role": "verification-engineer",
    "status": "PROPOSED",
    "artifact_candidates": [],
    "evidence_candidates": [{"evidence_type": "simulation", "summary": "regression passed"}],
    "claim_candidates": [{"statement": "byte order swapped", "claim_type": "HYPOTHESIS"}],
    "risk_proposals": ["CDC_CHANGE"],
    "blocker_proposals": [{"blocker_type": "ENVIRONMENT", "description": "sim license missing"}],
    "handoff_candidate": {"target_role": "integration-reviewer", "expected_output": "acceptance", "completion_criteria": "gate review"},
    "summary": "done",
}


def test_candidates_map_to_runtime_commands():
    commands = build_candidate_commands(VALIDATED, task(), "verification-engineer")
    types = [command["command_type"] for command in commands]
    assert types == ["REGISTER_EVIDENCE", "CREATE_CLAIM", "PROPOSE_RISK", "CREATE_BLOCKER", "SUBMIT_HANDOFF"]
    for command in commands:
        assert command["actor"] == "verification-engineer"
        assert command["target_ref"] == {"object_id": "task-1"}
        assert command["command_id"].startswith("cmd-")


def test_candidate_command_ids_are_idempotent():
    first = build_candidate_commands(VALIDATED, task(), "verification-engineer")
    second = build_candidate_commands(VALIDATED, task(), "verification-engineer")
    assert [c["command_id"] for c in first] == [c["command_id"] for c in second]


def test_candidate_ids_change_with_payload():
    changed = json.loads(json.dumps(VALIDATED))
    changed["claim_candidates"][0]["statement"] = "different"
    other = build_candidate_commands(changed, task(), "verification-engineer")
    base = build_candidate_commands(VALIDATED, task(), "verification-engineer")
    assert [c["command_id"] for c in other] != [c["command_id"] for c in base]


def test_risk_proposal_accepts_string_and_object():
    validated = {**VALIDATED, "evidence_candidates": [], "claim_candidates": [], "blocker_proposals": [], "handoff_candidate": None}
    validated["risk_proposals"] = ["CDC_CHANGE", {"risk_factor": "BASELINE_CHANGE"}]
    commands = build_candidate_commands(validated, task(), "orchestrator")
    assert [c["payload"]["risk_factor"] for c in commands] == ["CDC_CHANGE", "BASELINE_CHANGE"]
