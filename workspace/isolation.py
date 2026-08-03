"""Isolation for pilot writes: git worktree first, temp clone fallback.

The user's original workspace is never touched; write results are preserved as
a patch file (or left in the isolated worktree) and are never auto-merged.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .adapter import WorkspaceAdapterError, _git


class Isolation:
    def __init__(self, mode: str, root: Path, git_root: Path, cleanup: Any = None):
        self.mode = mode
        self.root = root
        self.git_root = git_root
        self._cleanup = cleanup

    def close(self) -> None:
        if self._cleanup is not None:
            self._cleanup()

    def __enter__(self) -> "Isolation":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class WorkspaceIsolation:
    """Creates isolated worktrees/clones and emits patches."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)

    def create(self, *, commit: str = "HEAD", mode: str = "worktree") -> Isolation:
        git_root = _git(self.repo_root, "rev-parse", "--show-toplevel").stdout.strip()
        git_root_path = Path(git_root)
        if mode == "worktree":
            target = Path(tempfile.mkdtemp(prefix="dc-isolation-")) / "wt"
            result = _git(git_root_path, "worktree", "add", "--detach", str(target), commit, check=False)
            if result.returncode != 0:
                raise WorkspaceAdapterError("WORKTREE_FAILED", result.stderr.strip() or result.stdout.strip())
            return Isolation("worktree", target, git_root_path, cleanup=lambda: _git(git_root_path, "worktree", "remove", "--force", str(target), check=False))
        if mode == "clone":
            target = Path(tempfile.mkdtemp(prefix="dc-clone-"))
            result = subprocess.run(
                ["git", "clone", "--no-checkout", "--no-local", str(git_root_path), str(target)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            )
            if result.returncode != 0:
                raise WorkspaceAdapterError("CLONE_FAILED", result.stderr.strip() or result.stdout.strip())
            checkout = subprocess.run(
                ["git", "-C", str(target), "checkout", "--detach", commit],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            )
            if checkout.returncode != 0:
                raise WorkspaceAdapterError("CLONE_CHECKOUT_FAILED", checkout.stderr.strip() or checkout.stdout.strip())
            import shutil

            return Isolation("clone", target, git_root_path, cleanup=lambda: shutil.rmtree(target, ignore_errors=True))
        raise WorkspaceAdapterError("ISOLATION_MODE_UNKNOWN", f"mode must be worktree or clone, got {mode!r}")

    def patch_from(self, isolation: Isolation, *, base: str = "HEAD", out: str | Path) -> Path:
        """Diff between the base commit and the isolated working tree."""
        patch_path = Path(out)
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "-C", str(isolation.root), "diff", base, "--"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        if result.returncode != 0:
            raise WorkspaceAdapterError("PATCH_FAILED", result.stderr.strip() or result.stdout.strip())
        patch_path.write_text(result.stdout, encoding="utf-8")
        return patch_path
