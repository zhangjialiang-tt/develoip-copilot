"""Convert validated role outputs into candidate Runtime Commands.

Candidates are proposals only: nothing here mutates state. Each candidate
command must still pass ownership, Approval, Baseline and Scope checks in
``Runtime.dispatch()``. Command IDs are content-derived so a resubmitted
candidate is idempotent.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

CANDIDATE_COMMAND_TYPES = {
    "artifact_candidates": "REGISTER_ARTIFACT",
    "evidence_candidates": "REGISTER_EVIDENCE",
    "claim_candidates": "CREATE_CLAIM",
    "risk_proposals": "PROPOSE_RISK",
    "blocker_proposals": "CREATE_BLOCKER",
    "handoff_candidate": "SUBMIT_HANDOFF",
}


def _command_id(task_id: str, command_type: str, actor: str, payload: dict[str, Any]) -> str:
    material = json.dumps({"task": task_id, "type": command_type, "actor": actor, "payload": payload}, sort_keys=True, ensure_ascii=False)
    return "cmd-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def _risk_payload(proposal: Any) -> dict[str, Any]:
    if isinstance(proposal, str):
        return {"risk_factor": proposal}
    if isinstance(proposal, dict) and proposal.get("risk_factor"):
        return {"risk_factor": proposal["risk_factor"]}
    raise ValueError("risk proposal must be a risk_factor string or object")


def build_candidate_commands(validated: dict[str, Any], task: dict[str, Any], actor: str) -> list[dict[str, Any]]:
    task_id = task["object_id"]
    commands: list[dict[str, Any]] = []

    def add(command_type: str, payload: dict[str, Any]) -> None:
        commands.append({
            "command_id": _command_id(task_id, command_type, actor, payload),
            "command_type": command_type,
            "actor": actor,
            "target_ref": {"object_id": task_id},
            "payload": payload,
        })

    for key, command_type in CANDIDATE_COMMAND_TYPES.items():
        candidate = validated.get(key)
        if candidate is None:
            continue
        items = candidate if isinstance(candidate, list) else [candidate]
        for item in items:
            if item is None:
                continue
            if not isinstance(item, dict):
                if command_type == "PROPOSE_RISK":
                    item = _risk_payload(item)
                else:
                    raise ValueError(f"{key} entries must be objects")
            if command_type == "PROPOSE_RISK":
                item = _risk_payload(item)
            add(command_type, dict(item))
    return commands
