from workspace.adapter import WorkspaceAdapter, WorkspaceAdapterError, file_sha256


def test_discover_git_root(git_repo):
    adapter = WorkspaceAdapter(git_repo)
    assert adapter.discover_git_root() == git_repo.resolve()


def test_discover_git_root_rejects_non_repo(tmp_path):
    adapter = WorkspaceAdapter(tmp_path / "nope")
    try:
        adapter.discover_git_root()
        assert False, "expected NOT_A_GIT_REPO"
    except WorkspaceAdapterError as error:
        assert error.code == "NOT_A_GIT_REPO"


def test_snapshot_captures_facts(git_repo):
    adapter = WorkspaceAdapter(git_repo)
    snapshot = adapter.snapshot(
        read_scope={"paths": ["rtl/qspi"]},
        relevant_paths=["rtl/qspi/qspi_driver.v"],
        tool_versions={"git": "2.0"},
        input_data_refs=["rtl/qspi/vectors.txt"],
    )
    assert snapshot["commit"]
    assert snapshot["branch"] in {"master", "main", None}
    assert snapshot["tracked_modified"] == []
    assert snapshot["untracked"] == []
    assert "rtl/qspi/qspi_driver.v" in snapshot["relevant_file_hashes"]
    assert snapshot["tool_versions"] == {"git": "2.0"}


def test_classification_matrix(git_repo):
    adapter = WorkspaceAdapter(git_repo)
    read_scope = {"paths": ["rtl/qspi"]}
    write_scope = {"paths": ["rtl/qspi"]}

    clean = adapter.snapshot(read_scope=read_scope, write_scope=write_scope)
    assert adapter.classify(clean) == "CLEAN"

    # modify a file inside the read scope
    (git_repo / "rtl" / "qspi" / "qspi_driver.v").write_text("module qspi; // changed\nendmodule\n", encoding="utf-8")
    related = adapter.snapshot(read_scope=read_scope, write_scope=write_scope)
    assert adapter.classify(related) == "CONFLICTING"  # inside write scope too

    # write scope empty -> related dirty
    related_no_write = adapter.snapshot(read_scope=read_scope, write_scope={"paths": []})
    assert adapter.classify(related_no_write) == "DIRTY_RELATED"

    # unrelated dirty
    from subprocess import run
    run(["git", "-C", str(git_repo), "checkout", "--", "rtl/qspi/qspi_driver.v"], check=True)
    (git_repo / "notes.txt").write_text("changed\n", encoding="utf-8")
    unrelated = adapter.snapshot(read_scope=read_scope, write_scope=write_scope)
    assert adapter.classify(unrelated) == "DIRTY_UNRELATED"


def test_classify_unknown_without_commit(tmp_path):
    adapter = WorkspaceAdapter(tmp_path)
    assert adapter.classify({"commit": None}) == "UNKNOWN"


def test_diff_before_after(git_repo):
    adapter = WorkspaceAdapter(git_repo)
    before = adapter.snapshot(relevant_paths=["rtl/qspi/qspi_driver.v"])
    (git_repo / "rtl" / "qspi" / "qspi_driver.v").write_text("module qspi; // v2\nendmodule\n", encoding="utf-8")
    after = adapter.snapshot(relevant_paths=["rtl/qspi/qspi_driver.v"])
    diff = adapter.diff_before_after(before, after)
    assert diff["modified"] == ["rtl/qspi/qspi_driver.v"]
    assert diff["branch_changed"] is False
    # restore to keep the fixture repo clean for other tests
    import subprocess
    subprocess.run(["git", "-C", str(git_repo), "checkout", "--", "rtl/qspi/qspi_driver.v"], check=True)


def test_file_sha256_deterministic(tmp_path):
    path = tmp_path / "a.v"
    path.write_text("module a; endmodule\n", encoding="utf-8")
    assert file_sha256(path) == file_sha256(path)
    assert len(file_sha256(path)) == 64
