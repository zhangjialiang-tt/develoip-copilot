from workspace.adapter import WorkspaceAdapter
from workspace.baseline import WorkspaceBaseline


def _snapshot(git_repo, adapter):
    return adapter.snapshot(relevant_paths=["rtl/qspi/qspi_driver.v"], tool_versions={"git": "2.0"}, input_data_refs=["rtl/qspi/vectors.txt"])


def test_baseline_capture_is_deterministic(git_repo):
    adapter = WorkspaceAdapter(git_repo)
    first = WorkspaceBaseline(adapter).capture(_snapshot(git_repo, adapter))
    second = WorkspaceBaseline(adapter).capture(_snapshot(git_repo, adapter))
    assert first == second
    assert ":" in first["code_revision_or_workspace_snapshot"]
    commit, fingerprint = first["code_revision_or_workspace_snapshot"].split(":", 1)
    assert len(commit) >= 7 and len(fingerprint) == 16
    assert first["toolchain_versions"] == {"git": "2.0"}
    assert first["input_data_refs"] == ["rtl/qspi/vectors.txt"]
    assert first["files"] == [{"path": "rtl/qspi/qspi_driver.v", "sha256": first["files"][0]["sha256"]}]


def test_baseline_changes_when_file_changes(git_repo):
    adapter = WorkspaceAdapter(git_repo)
    baseline_a = WorkspaceBaseline(adapter).capture(_snapshot(git_repo, adapter))
    (git_repo / "rtl" / "qspi" / "qspi_driver.v").write_text("module qspi; // v2\nendmodule\n", encoding="utf-8")
    baseline_b = WorkspaceBaseline(adapter).capture(_snapshot(git_repo, adapter))
    assert baseline_a["code_revision_or_workspace_snapshot"] != baseline_b["code_revision_or_workspace_snapshot"]
    import subprocess
    subprocess.run(["git", "-C", str(git_repo), "checkout", "--", "rtl/qspi/qspi_driver.v"], check=True)


def test_baseline_requires_commit(git_repo):
    adapter = WorkspaceAdapter(git_repo)
    try:
        WorkspaceBaseline(adapter).capture({"commit": None, "relevant_file_hashes": {}})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_fingerprint_stable():
    baseline = {"code_revision_or_workspace_snapshot": "abc:def"}
    assert WorkspaceBaseline.fingerprint(baseline) == "abc:def"
