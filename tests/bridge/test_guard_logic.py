from runtime.omp_bridge import classify_bash, normalize_path


def test_read_only_commands_are_read():
    for command in ["cat foo.v", "git status", "git diff", "ls -la", "python -m pytest -q", "grep x file"]:
        assert classify_bash(command)[0] == "READ", command


def test_in_place_editing_is_write_likely():
    for command in ["sed -i 's/a/b/' f.txt", "sed --in-place s/a/b/ f.txt"]:
        assert classify_bash(command)[0] == "WRITE_LIKELY", command


def test_destructive_and_copy_commands_are_write_likely():
    for command in ["rm foo", "mv a b", "cp a b", "del file.txt", "chmod +x run.sh", "truncate -s 0 log"]:
        assert classify_bash(command)[0] == "WRITE_LIKELY", command


def test_redirection_is_write_likely():
    for command in ["echo x > out.txt", "cat a >> b.txt", "python tool.py > result.log"]:
        assert classify_bash(command)[0] == "WRITE_LIKELY", command


def test_git_working_tree_mutations_are_write_likely():
    for command in ["git checkout -- file.v", "git restore .", "git reset --hard", "git clean -fd", "git push origin", "git commit -m x"]:
        assert classify_bash(command)[0] == "WRITE_LIKELY", command


def test_powershell_write_cmdlets_are_write_likely():
    for command in ["Set-Content -Path a -Value b", "Remove-Item x", "New-Item -Path y", "Out-File z.txt"]:
        assert classify_bash(command)[0] == "WRITE_LIKELY", command


def test_normalize_path_unifies_separators():
    assert normalize_path("C:\\work\\pilot\\") == "C:/work/pilot"
    assert normalize_path(" a/b/ ") == "a/b"
