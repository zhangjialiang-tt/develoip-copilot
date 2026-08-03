from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from .errors import ContractError

ROLE_RESPONSE_FIELDS = {
    "status",
    "artifact_candidates",
    "evidence_candidates",
    "claim_candidates",
    "risk_proposals",
    "blocker_proposals",
    "handoff_candidate",
    "summary",
}
REQUIRED_REQUEST_FIELDS = ("role", "task_ref", "scope", "approval_refs", "baseline_ref", "expected_output", "completion_criteria")


class RoleInvocationLayer:
    """Role boundary; handlers propose structured objects, Runtime activates them."""

    def __init__(self):
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(self, role: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._handlers[role] = handler

    def invoke(self, request: dict[str, Any]) -> dict[str, Any]:
        for field in REQUIRED_REQUEST_FIELDS:
            if field not in request:
                raise ContractError("ROLE_REQUEST_INVALID", f"Missing role request field: {field}")
        handler = self._handlers.get(request["role"])
        if handler is None:
            raise ContractError("ROLE_NOT_REGISTERED", f"No handler for role: {request['role']}")
        candidate = handler(deepcopy(request))
        if not isinstance(candidate, dict):
            raise ContractError("ROLE_RESPONSE_INVALID", "Role response must be an object")
        if any(key in candidate for key in {"gate_status", "claim_status", "closure_status", "project_status"}):
            raise ContractError("ROLE_DIRECT_STATE_WRITE_FORBIDDEN", "Role may not return Derived Result writes")
        response = {
            "role": request["role"],
            "status": "PROPOSED",
            "artifact_candidates": [],
            "evidence_candidates": [],
            "claim_candidates": [],
            "risk_proposals": [],
            "blocker_proposals": [],
            "handoff_candidate": None,
            "summary": "",
        }
        response.update({key: deepcopy(value) for key, value in candidate.items() if key in ROLE_RESPONSE_FIELDS})
        return response
