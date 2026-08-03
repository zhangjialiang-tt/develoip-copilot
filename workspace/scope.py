"""Scope utilities shared by the Workspace Adapter, Bridge guard and Runtime.

Path normalization and scope-membership are contract-relevant: the guard and
the candidate-write-scope checks MUST agree on what "inside scope" means.
"""
from __future__ import annotations

from typing import Any, Iterable


def normalize_path(value: str) -> str:
    return str(value).replace("\\", "/").strip().rstrip("/")


def path_in_scope(path: str, scope: dict[str, Any] | None) -> bool:
    """True when ``path`` lies inside one of ``scope["paths"]`` roots."""
    if not scope:
        return False
    normalized = normalize_path(path)
    if not normalized:
        return False
    for root in scope.get("paths", []):
        root_path = normalize_path(root)
        if not root_path:
            continue
        if normalized == root_path or normalized.startswith(root_path + "/"):
            return True
    return False


def scopes_overlap(a: dict[str, Any] | None, b: dict[str, Any] | None) -> bool:
    """True when any path root of ``a`` and ``b`` overlap (one contains the other)."""
    if not a or not b:
        return False
    paths_a = {normalize_path(p) for p in a.get("paths", []) if normalize_path(p)}
    paths_b = {normalize_path(p) for p in b.get("paths", []) if normalize_path(p)}
    for root_a in paths_a:
        for root_b in paths_b:
            if root_a == root_b or root_a.startswith(root_b + "/") or root_b.startswith(root_a + "/"):
                return True
    return False


def validate_scope(scope: dict[str, Any] | None) -> list[str]:
    """Return a list of problems; empty list means the scope is well-formed."""
    problems: list[str] = []
    if not isinstance(scope, dict):
        return ["scope must be an object"]
    paths = scope.get("paths", [])
    if not isinstance(paths, list):
        return ["scope.paths must be a list"]
    for path in paths:
        if not isinstance(path, str) or not path.strip():
            problems.append(f"scope.paths contains invalid entry: {path!r}")
    return problems


def outside_scope_paths(paths: Iterable[str], scope: dict[str, Any] | None) -> list[str]:
    """Return the subset of ``paths`` that fall outside ``scope``."""
    return [path for path in paths if not path_in_scope(path, scope)]
