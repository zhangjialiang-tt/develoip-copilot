"""Shared git-repo fixture for workspace tests."""
import subprocess
from pathlib import Path

import pytest


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    (repo / "rtl").mkdir()
    (repo / "rtl" / "qspi").mkdir()
    (repo / "rtl" / "qspi" / "qspi_driver.v").write_text("module qspi; endmodule\n", encoding="utf-8")
    (repo / "rtl" / "other" ).mkdir()
    (repo / "rtl" / "other" / "unrelated.v").write_text("module unrelated; endmodule\n", encoding="utf-8")
    (repo / "notes.txt").write_text("hello\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "initial")
    return repo
