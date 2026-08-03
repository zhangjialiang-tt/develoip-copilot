"""Baseline capture for the pilot workspace.

Produces a Runtime-Baseline-compatible payload from adapter facts: the git
commit is the code revision anchor, plus deterministic hashes of the scoped
relevant files, tool versions and input references. Capture is read-only and
repeatable (sorted, stable digest).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .adapter import WorkspaceAdapter, file_sha256
from .scope import normalize_path


class WorkspaceBaseline:
    def __init__(self, adapter: WorkspaceAdapter):
        self.adapter = adapter

    def capture(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        """Build a Runtime Baseline payload from a workspace snapshot."""
        commit = snapshot.get("commit")
        if not commit:
            raise ValueError("snapshot has no commit; workspace must be a git repository")
        digest = hashlib.sha256()
        digest.update(commit.encode("utf-8"))
        for relative in sorted(snapshot.get("relevant_file_hashes", {})):
            digest.update(relative.encode("utf-8"))
            digest.update(snapshot["relevant_file_hashes"][relative].encode("utf-8"))
        return {
            "code_revision_or_workspace_snapshot": f"{commit}:{digest.hexdigest()[:16]}",
            "configuration_set": snapshot.get("configuration_set", {}),
            "toolchain_versions": snapshot.get("tool_versions", {}),
            "input_data_refs": snapshot.get("input_data_refs", []),
            "dependency_refs": [],
            "files": [{"path": path, "sha256": snapshot["relevant_file_hashes"][path]} for path in sorted(snapshot.get("relevant_file_hashes", {}))],
        }

    @staticmethod
    def fingerprint(baseline: dict[str, Any]) -> str:
        return baseline.get("code_revision_or_workspace_snapshot", "")
