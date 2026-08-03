from workspace.adapter import WorkspaceAdapter
from workspace.isolation import WorkspaceIsolation


def test_worktree_isolation_does_not_touch_original(git_repo):
    original_state = (git_repo / "rtl" / "qspi" / "qspi_driver.v").read_text(encoding="utf-8")
    isolation = WorkspaceIsolation(git_repo)
    with isolation.create(mode="worktree") as wt:
        assert wt.root.is_dir()
        assert (wt.root / "rtl" / "qspi" / "qspi_driver.v").exists()
        # modify the isolated copy only
        (wt.root / "rtl" / "qspi" / "qspi_driver.v").write_text("module qspi; // isolated\nendmodule\n", encoding="utf-8")
        patch = isolation.patch_from(wt, out=wt.root / "change.patch")
        assert "isolated" in patch.read_text(encoding="utf-8")
    # original untouched after isolation close
    assert (git_repo / "rtl" / "qspi" / "qspi_driver.v").read_text(encoding="utf-8") == original_state


def test_clone_isolation_fallback(git_repo):
    isolation = WorkspaceIsolation(git_repo)
    with isolation.create(mode="clone") as clone:
        assert clone.root.is_dir()
        assert (clone.root / "rtl" / "qspi" / "qspi_driver.v").exists()
        (clone.root / "rtl" / "qspi" / "qspi_driver.v").write_text("module qspi; // clone\nendmodule\n", encoding="utf-8")
        patch = isolation.patch_from(clone, out=clone.root / "change.patch")
        assert "clone" in patch.read_text(encoding="utf-8")


def test_unknown_isolation_mode_rejected(git_repo):
    isolation = WorkspaceIsolation(git_repo)
    try:
        isolation.create(mode="overlay")
        assert False, "expected ISOLATION_MODE_UNKNOWN"
    except Exception as error:
        assert getattr(error, "code", None) == "ISOLATION_MODE_UNKNOWN"
