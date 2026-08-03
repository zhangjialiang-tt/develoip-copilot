from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import ContractError
from .persistence import JsonlEventStore


class BaselineCapture:
    def capture(self, root: str | Path, *, configuration_set: dict[str, Any], toolchain_versions: dict[str, str], input_data_refs: list[str], dependency_refs: list[str] | None = None) -> dict[str, Any]:
        root_path = Path(root)
        files = []
        digest = hashlib.sha256()
        for path in sorted(root_path.rglob("*")):
            if not path.is_file() or ".git" in path.parts:
                continue
            relative = path.relative_to(root_path).as_posix()
            content = path.read_bytes()
            file_hash = hashlib.sha256(content).hexdigest()
            files.append({"path": relative, "sha256": file_hash})
            digest.update(relative.encode("utf-8"))
            digest.update(content)
        return {
            "code_revision_or_workspace_snapshot": digest.hexdigest(),
            "configuration_set": configuration_set,
            "toolchain_versions": toolchain_versions,
            "input_data_refs": input_data_refs,
            "dependency_refs": dependency_refs or [],
            "files": files,
        }


class TestResultParser:
    def parse(self, raw: str | dict[str, Any]) -> dict[str, Any]:
        result = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(result, dict) or not isinstance(result.get("passed"), bool):
            raise ContractError("TOOL_RESULT_INVALID", "Test result must contain boolean passed")
        return {"passed": result["passed"], "actual": result.get("actual"), "expected": result.get("expected"), **({"coverage": result["coverage"]} if "coverage" in result else {})}


class EventStoreValidator:
    def validate(self, store: JsonlEventStore) -> dict[str, Any]:
        events = store.events()
        valid = all(record.get("sequence") == index for index, record in enumerate(events, start=1))
        return {"valid": valid, "last_sequence": len(events), "event_count": len(events)}


class ScopeDiff:
    def compare(self, before: list[str], after: list[str]) -> dict[str, Any]:
        before_set, after_set = set(before), set(after)
        return {"added": sorted(after_set - before_set), "removed": sorted(before_set - after_set), "unchanged": sorted(before_set & after_set)}


class ApprovalAdapter:
    """Small confirmation API; it delegates every decision to Runtime.dispatch()."""

    def request(self, runtime, command: dict[str, Any]) -> dict[str, Any]:
        return runtime.dispatch(command)

    def grant(self, runtime, command: dict[str, Any]) -> dict[str, Any]:
        return runtime.dispatch(command)

    def reject(self, runtime, command: dict[str, Any]) -> dict[str, Any]:
        return runtime.dispatch(command)

    def revoke(self, runtime, command: dict[str, Any]) -> dict[str, Any]:
        return runtime.dispatch(command)


class RecordReferenceValidator:
    def validate(self, record: dict[str, Any], runtime) -> dict[str, Any]:
        missing = []
        for object_type, refs in record.get("references", {}).items():
            for object_id in refs:
                try:
                    runtime.query(object_id, object_type)
                except ContractError:
                    missing.append({"object_type": object_type, "object_id": object_id})
        return {"valid": not missing, "missing": missing}
