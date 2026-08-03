import json

import pytest

from runtime.errors import PersistenceError
from runtime.persistence import JsonlEventStore


def _event(event_id: str, command_id: str, event_type: str = "TASK_CREATED"):
    return {
        "event_id": event_id,
        "event_type": event_type,
        "aggregate_type": "Task",
        "aggregate_id": "task-1",
        "actor": "orchestrator",
        "payload": {"object_id": "task-1"},
    }


def test_event_store_is_append_only_and_command_retry_is_idempotent(tmp_path):
    path = tmp_path / "events.jsonl"
    store = JsonlEventStore(path)

    first = store.append("cmd-1", _event("event-1", "cmd-1"), {"accepted": True})
    retry = store.append("cmd-1", _event("event-should-not-exist", "cmd-1"), {"accepted": False})

    assert first == retry
    assert len(store.events()) == 1
    assert store.events()[0]["sequence"] == 1

    restored = JsonlEventStore(path)
    assert restored.events() == store.events()
    assert restored.result_for("cmd-1") == {"accepted": True}


def test_event_store_rejects_non_contiguous_sequence(tmp_path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"record_type": "runtime_event", "sequence": 1, "command_id": "cmd-1", "event": _event("event-1", "cmd-1"), "result": {}}),
                json.dumps({"record_type": "runtime_event", "sequence": 3, "command_id": "cmd-2", "event": _event("event-2", "cmd-2"), "result": {}}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(PersistenceError) as error:
        JsonlEventStore(path)

    assert error.value.code == "EVENT_SEQUENCE_INVALID"
