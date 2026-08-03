import json
from typing import Any

from .errors import ContractError

SCHEMA_VERSION = 1
CORE_OBJECT_TYPES = (
    "Task",
    "Baseline",
    "Approval",
    "Artifact",
    "Evidence",
    "Claim",
    "Handoff",
    "Acceptance",
    "Waiver",
    "Blocker",
    "ClosureGate",
    "RuntimeEvent",
)

ENUM_FIELDS = {
    "execution_status": {
        "PROPOSED", "READY", "RUNNING", "BLOCKED", "AWAITING_APPROVAL",
        "AWAITING_VALIDATION", "REWORK_REQUIRED", "FINISHED", "CANCELLED",
    },
    "acceptance_status": {"NOT_REVIEWED", "ACCEPTED", "REJECTED", "CONDITIONALLY_ACCEPTED"},
    "status": {
        "REQUESTED", "GRANTED", "REJECTED", "REVOKED", "INVALIDATED", "PROPOSED",
        "SUPPORTED", "CONTRADICTED", "SUPERSEDED", "VALID", "DEGRADED", "WAIVED",
        "SATISFIED", "UNSATISFIED", "NOT_REQUIRED",
    },
    "claim_type": {"FACT", "OBSERVATION", "INFERENCE", "DECISION", "HYPOTHESIS"},
    "reproducibility_level": {"E0", "E1", "E2", "E3"},
    "independence": {"SELF_PRODUCED", "INDEPENDENT_ROLE", "INDEPENDENT_METHOD", "EXTERNAL_SOURCE"},
}


def validate_object(value: dict[str, Any], expected_type: str | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("INVALID_OBJECT", "Object must be a JSON object")
    object_type = value.get("object_type")
    if object_type not in CORE_OBJECT_TYPES:
        raise ContractError("INVALID_OBJECT_TYPE", f"Unknown object_type: {object_type!r}")
    if expected_type and object_type != expected_type:
        raise ContractError("REFERENCE_TYPE_MISMATCH", f"Expected {expected_type}, got {object_type}")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ContractError("SCHEMA_VERSION_UNSUPPORTED", "Only schema_version=1 is supported")
    for field in ("object_id", "created_at", "created_by"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise ContractError("REQUIRED_FIELD_MISSING", f"Missing required field: {field}")
    for field, allowed in ENUM_FIELDS.items():
        if field not in value:
            continue
        candidate = value[field]
        candidates = candidate if field == "independence" and isinstance(candidate, list) else [candidate]
        if any(item not in allowed for item in candidates):
            raise ContractError("INVALID_ENUM", f"Invalid {field}: {candidate!r}")
    try:
        json.dumps(value, sort_keys=True)
    except (TypeError, ValueError) as error:
        raise ContractError("NOT_JSON_SERIALIZABLE", str(error)) from error
    return value


def round_trip_object(value: dict[str, Any]) -> dict[str, Any]:
    validate_object(value)
    restored = json.loads(json.dumps(value, sort_keys=True))
    validate_object(restored)
    return restored
