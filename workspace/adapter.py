"""Workspace Adapter: read-only view of the pilot repository.

Never mutates the user's workspace. Produces the facts needed for Baseline
capture, scope enforcement and isolation: git root/branch/commit, tracked /
untracked / modified / ignored files, submodules, relevant file hashes,
tool versions and the workspace classification.

Classification semantics (plan §13.4):

- CLEAN           tracked tree matches HEAD, no untracked/ignored surprises
- DIRTY_RELATED   modifications/untracked files inside the read scope
- DIRTY_UNRELATED modifications/untracked files outside the read scope
- CONFLICTING     modifications overlap candidate write scope (WRITE forbidden)
- UNKNOWN         repository state cannot be determined (WRITE forbidden)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .scope import normalize_path, path_in_scope, scopes_overlap

CLASSIFICATIONS = ("CLEAN", "DIRTY_RELATED", "DIRTY_UNRELATED", "CONFLICTING", "UNKNOWN")
WRITE_FORBIDDEN = {"CONFLICTING", "UNKNOWN"}


class WorkspaceAdapterError(Exception):
    """A deterministic adapter failure."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


class WorkspaceAdapter:
    """Read-only facts about one pilot repository."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)

    def discover_git_root(self) -> Path:
        result = _git(self.repo_root, "rev-parse", "--show-toplevel", check=False)
        if result.returncode != 0 or not result.stdout.strip():
            raise WorkspaceAdapterError("NOT_A_GIT_REPO", f"{self.repo_root} is not inside a git repository")
        return Path(result.stdout.strip())

    def snapshot(self, *, read_scope: dict[str, Any] | None = None, write_scope: dict[str, Any] | None = None, relevant_paths: list[str] | None = None, tool_versions: dict[str, str] | None = None, input_data_refs: list[str] | None = None) -> dict[str, Any]:
        """Capture the full workspace facts; never modifies anything."""
        git_root = self.discover_git_root()
        branch_result = _git(git_root, "branch", "--show-current", check=False)
        head_result = _git(git_root, "rev-parse", "HEAD", check=False)
        status_result = _git(git_root, "status", "--porcelain=v1", check=False)
        untracked_result = _git(git_root, "ls-files", "--others", "--exclude-standard", check=False)
        ignored_result = _git(git_root, "status", "--porcelain=v1", "--ignored", check=False)
        submodule_result = _git(git_root, "submodule", "status", check=False)

        tracked_modified: list[str] = []
        untracked: list[str] = []
        for line in status_result.stdout.splitlines():
            if not line or len(line) < 3:
                continue
            code, path = line[:2], line[3:]
            if code.strip() and not code.startswith("!!"):
                tracked_modified.append(path)
            elif code == "??":
                untracked.append(path)
        ignored = [line[3:] for line in ignored_result.stdout.splitlines() if line.startswith("!!")]

        hashes: dict[str, str] = {}
        for relative in relevant_paths or []:
            candidate = git_root / relative
            if candidate.is_file():
                hashes[normalize_path(relative)] = file_sha256(candidate)

        return {
            "git_root": str(git_root),
            "branch": branch_result.stdout.strip() or None,
            "commit": head_result.stdout.strip() if head_result.returncode == 0 else None,
            "tracked_modified": sorted(tracked_modified),
            "untracked": sorted(untracked),
            "ignored": sorted(ignored),
            "submodules": [line for line in submodule_result.stdout.splitlines() if line.strip()],
            "relevant_file_hashes": hashes,
            "tool_versions": tool_versions or {},
            "input_data_refs": input_data_refs or [],
            "read_scope": read_scope,
            "candidate_write_scope": write_scope,
        }

    def classify(self, snapshot: dict[str, Any]) -> str:
        """Workspace classification per plan §13.4."""
        if snapshot.get("commit") is None:
            return "UNKNOWN"
        read_scope = snapshot.get("read_scope")
        write_scope = snapshot.get("candidate_write_scope")
        modified_in_scope = [p for p in snapshot.get("tracked_modified", []) if path_in_scope(p, read_scope)]
        modified_outside = [p for p in snapshot.get("tracked_modified", []) if not path_in_scope(p, read_scope)]
        untracked_in_scope = [p for p in snapshot.get("untracked", []) if path_in_scope(p, read_scope)]
        untracked_outside = [p for p in snapshot.get("untracked", []) if not path_in_scope(p, read_scope)]

        conflict = [p for p in snapshot.get("tracked_modified", []) if path_in_scope(p, write_scope)] if write_scope else []
        if conflict or (write_scope and any(path_in_scope(p, write_scope) for p in snapshot.get("untracked", []))):
            return "CONFLICTING"

        if not modified_in_scope and not untracked_in_scope:
            if modified_outside or untracked_outside:
                return "DIRTY_UNRELATED"
            return "CLEAN"
        return "DIRTY_RELATED"

    def diff_before_after(self, before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
        """Compare two snapshots (e.g. pre/post isolation work)."""
        before_hashes = before.get("relevant_file_hashes", {})
        after_hashes = after.get("relevant_file_hashes", {})
        return {
            "added": sorted(set(after_hashes) - set(before_hashes)),
            "removed": sorted(set(before_hashes) - set(after_hashes)),
            "modified": sorted(path for path in set(before_hashes) & set(after_hashes) if before_hashes[path] != after_hashes[path]),
            "branch_changed": before.get("commit") != after.get("commit"),
        }

    def to_json(self, snapshot: dict[str, Any]) -> str:
        return json.dumps(snapshot, sort_keys=True, ensure_ascii=False, indent=2)
