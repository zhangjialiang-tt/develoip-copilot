import subprocess
from pathlib import Path

import pytest

from workspace.scope import normalize_path, outside_scope_paths, path_in_scope, scopes_overlap, validate_scope


def test_normalize_path_unifies_separators():
    assert normalize_path("a\\b\\c") == "a/b/c"
    assert normalize_path(" a/b/ ") == "a/b"
    assert normalize_path("") == ""


def test_path_in_scope_prefix_rules():
    scope = {"paths": ["rtl/qspi"]}
    assert path_in_scope("rtl/qspi", scope)
    assert path_in_scope("rtl/qspi/qspi_driver.v", scope)
    assert not path_in_scope("rtl/qspi_driver.v", scope)
    assert not path_in_scope("rtl/other/a.v", scope)
    assert not path_in_scope("rtl/qspi2/a.v", scope)


def test_path_in_scope_empty_or_none():
    assert not path_in_scope("a/b", None)
    assert not path_in_scope("a/b", {"paths": []})
    assert not path_in_scope("", {"paths": ["a"]})


def test_scopes_overlap():
    a = {"paths": ["rtl/qspi"]}
    b = {"paths": ["rtl/qspi/tb"]}
    c = {"paths": ["rtl/other"]}
    assert scopes_overlap(a, b)
    assert scopes_overlap(b, a)
    assert not scopes_overlap(a, c)
    assert not scopes_overlap(a, None)


def test_validate_scope():
    assert validate_scope({"paths": ["a", "b"]}) == []
    assert validate_scope({"paths": []}) == []
    problems = validate_scope({"paths": ["a", ""]})
    assert len(problems) == 1
    assert validate_scope(None) != []
    assert validate_scope({"paths": "not-a-list"}) != []


def test_outside_scope_paths():
    scope = {"paths": ["rtl/qspi"]}
    assert outside_scope_paths(["rtl/qspi/a.v", "rtl/other/b.v"], scope) == ["rtl/other/b.v"]
