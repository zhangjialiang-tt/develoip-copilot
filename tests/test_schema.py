import pytest

from runtime.schema import CORE_OBJECT_TYPES, SCHEMA_VERSION, round_trip_object, validate_object
from runtime.errors import ContractError


def test_core_objects_round_trip_with_explicit_schema_version():
    for object_type in CORE_OBJECT_TYPES:
        value = {
            "object_id": f"{object_type.lower()}-1",
            "object_type": object_type,
            "schema_version": SCHEMA_VERSION,
            "created_at": "2026-08-03T00:00:00Z",
            "created_by": "test",
        }
        restored = round_trip_object(value)
        assert restored == value
        assert restored["object_type"] == object_type


def test_invalid_enum_is_rejected_at_schema_boundary():
    value = {
        "object_id": "task-1",
        "object_type": "Task",
        "schema_version": SCHEMA_VERSION,
        "created_at": "2026-08-03T00:00:00Z",
        "created_by": "test",
        "execution_status": "NOT_A_STATUS",
    }

    with pytest.raises(ContractError) as error:
        validate_object(value)

    assert error.value.code == "INVALID_ENUM"
