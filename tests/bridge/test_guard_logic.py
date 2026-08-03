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


from runtime.omp_bridge import _bash_write_targets


def test_bash_write_targets_redirection():
    assert _bash_write_targets("echo x > out.txt") == ["out.txt"]
    assert _bash_write_targets("cat a >> b.log") == ["b.log"]
    assert _bash_write_targets("cmd 2> err.txt 1> out.txt") == ["err.txt", "out.txt"]
    assert _bash_write_targets("ls >pilot/x.txt") == ["pilot/x.txt"]


def test_bash_write_targets_option_and_dd():
    assert _bash_write_targets("dd of=image.bin") == ["image.bin"]
    assert _bash_write_targets("tool -o result.v") == ["result.v"]


def test_bash_write_targets_copy_destination():
    assert _bash_write_targets("cp common/rtl/dev/qspi_flash/a.v /tmp/x/") == ["/tmp/x/"]
    assert _bash_write_targets("mv a.v pilot/rtl/") == ["pilot/rtl/"]
    assert _bash_write_targets("cp -r src dst") == ["dst"]


def test_bash_write_targets_sed_and_git():
    assert _bash_write_targets("sed -i 's/a/b/' pilot/rtl/a.v") == ["pilot/rtl/a.v"]
    assert _bash_write_targets("git restore pilot/rtl/a.v other.v") == ["pilot/rtl/a.v", "other.v"]
    assert _bash_write_targets("git checkout -- a.v") == ["a.v"]


def test_bash_write_targets_source_path_not_target():
    # source path in a cp command must NOT be treated as a write target
    assert _bash_write_targets("cp common/rtl/dev/qspi_flash/qspi_driver_new.v /tmp/dc/x/") == ["/tmp/dc/x/"]
