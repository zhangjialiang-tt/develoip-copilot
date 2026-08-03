import json
from pathlib import Path
from typing import Any

from .errors import PersistenceError


class JsonlEventStore:
    """Small append-only store for RuntimeEvent records."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else None
        self._records: list[dict[str, Any]] = []
        self._by_command: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise PersistenceError("EVENT_STORE_READ_FAILED", str(error)) from error
        expected_sequence = 1
        event_ids: set[str] = set()
        for raw in lines:
            if not raw.strip():
                continue
            try:
                record = json.loads(raw)
            except json.JSONDecodeError as error:
                raise PersistenceError("EVENT_STORE_INVALID_JSON", str(error)) from error
            if record.get("record_type") != "runtime_event":
                raise PersistenceError("EVENT_RECORD_TYPE_INVALID", "Event store contains an unknown record type")
            if record.get("sequence") != expected_sequence:
                raise PersistenceError("EVENT_SEQUENCE_INVALID", f"Expected sequence {expected_sequence}")
            event = record.get("event") or {}
            event_id = event.get("event_id")
            command_id = record.get("command_id")
            if not event_id or event_id in event_ids:
                raise PersistenceError("EVENT_ID_INVALID", "Event IDs must be present and unique")
            if not command_id:
                raise PersistenceError("COMMAND_ID_MISSING", "Every event record needs command_id")
            event_ids.add(event_id)
            self._records.append(record)
            self._by_command[command_id] = record
            expected_sequence += 1

    def append(self, command_id: str, event: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        existing = self._by_command.get(command_id)
        if existing is not None:
            return existing
        if not command_id or not isinstance(event, dict):
            raise PersistenceError("EVENT_APPEND_INVALID", "command_id and event are required")
        record = {
            "record_type": "runtime_event",
            "sequence": len(self._records) + 1,
            "command_id": command_id,
            "event": event,
            "result": result,
        }
        self._write_line(record)
        self._records.append(record)
        self._by_command[command_id] = record
        return record

    def _write_line(self, record: dict[str, Any]) -> None:
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        except OSError as error:
            raise PersistenceError("EVENT_STORE_WRITE_FAILED", str(error)) from error

    def events(self) -> list[dict[str, Any]]:
        return [json.loads(json.dumps(record)) for record in self._records]

    def result_for(self, command_id: str) -> dict[str, Any] | None:
        record = self._by_command.get(command_id)
        if record is None:
            return None
        return json.loads(json.dumps(record["result"]))

    def last_sequence(self) -> int:
        return len(self._records)
