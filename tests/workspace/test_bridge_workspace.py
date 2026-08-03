"""Bridge integration tests: workspace_status, capture_baseline, guard classification."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)


class BridgeProcess:
    def __init__(self, state_dir: Path, config: dict):
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "runtime.omp_bridge", "--stdio", "--state-dir", str(state_dir)],
            cwd=REPO_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        self.seq = 0

    def request(self, op: str, params: dict | None = None, *, expect_ok: bool = True):
        self.seq += 1
        request_id = f"t{self.seq}"
        self.proc.stdin.write(json.dumps({"id": request_id, "op": op, "params": params or {}}) + "\n")
        self.proc.stdin.flush()
        frame = json.loads(self.proc.stdout.readline())
        assert frame["id"] == request_id
        if expect_ok:
            assert frame["ok"], frame
            return frame["result"]
        return frame["error"]

    def stop(self):
        if self.proc.poll() is None:
            try:
                self.request("shutdown")
            except Exception:
                pass
            self.proc.wait(timeout=10)


def make_pilot_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "pilot"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "t")
    (repo / "common").mkdir()
    (repo / "common" / "rtl").mkdir()
    (repo / "common" / "rtl" / "qspi_flash").mkdir()
    (repo / "common" / "rtl" / "qspi_flash" / "qspi_driver_new.v").write_text("module qspi; endmodule\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def test_workspace_status_reports_real_classification(tmp_path):
    pilot = make_pilot_repo(tmp_path)
    config = {
        "pilot_repository": str(pilot),
        "read_scope": {"paths": ["common/rtl/qspi_flash"]},
        "candidate_write_scope": {"paths": []},
        "relevant_paths": ["common/rtl/qspi_flash/qspi_driver_new.v"],
        "tool_versions": {"git": "2.0"},
        "input_data_refs": [],
    }
    bridge = BridgeProcess(tmp_path / "state", config)
    try:
        status = bridge.request("workspace_status")
        assert status["pilot_connected"] is True
        assert status["workspace_classification"] == "CLEAN"
        assert status["commit"]
    finally:
        bridge.stop()


def test_workspace_status_reports_dirty_related(tmp_path):
    pilot = make_pilot_repo(tmp_path)
    (pilot / "common" / "rtl" / "qspi_flash" / "qspi_driver_new.v").write_text("module qspi; // dirty\nendmodule\n", encoding="utf-8")
    config = {
        "pilot_repository": str(pilot),
        "read_scope": {"paths": ["common/rtl/qspi_flash"]},
        "candidate_write_scope": {"paths": []},
        "relevant_paths": ["common/rtl/qspi_flash/qspi_driver_new.v"],
    }
    bridge = BridgeProcess(tmp_path / "state", config)
    try:
        status = bridge.request("workspace_status")
        assert status["workspace_classification"] == "DIRTY_RELATED"
    finally:
        bridge.stop()


def test_capture_baseline_returns_runtime_compatible_payload(tmp_path):
    pilot = make_pilot_repo(tmp_path)
    config = {
        "pilot_repository": str(pilot),
        "read_scope": {"paths": ["common/rtl/qspi_flash"]},
        "candidate_write_scope": {"paths": []},
        "relevant_paths": ["common/rtl/qspi_flash/qspi_driver_new.v"],
        "tool_versions": {"modelsim": "2020.4"},
        "input_data_refs": ["common/rtl/qspi_flash/MEM.TXT"],
    }
    bridge = BridgeProcess(tmp_path / "state", config)
    try:
        result = bridge.request("capture_baseline")
        baseline = result["baseline"]
        assert ":" in baseline["code_revision_or_workspace_snapshot"]
        assert baseline["toolchain_versions"] == {"modelsim": "2020.4"}
        assert baseline["input_data_refs"] == ["common/rtl/qspi_flash/MEM.TXT"]
        assert baseline["files"][0]["path"] == "common/rtl/qspi_flash/qspi_driver_new.v"
        assert result["classification"] == "CLEAN"
    finally:
        bridge.stop()


def test_guard_blocks_conflicting_workspace_writes(tmp_path):
    pilot = make_pilot_repo(tmp_path)
    # dirty inside candidate write scope -> CONFLICTING -> WRITE forbidden
    (pilot / "common" / "rtl" / "qspi_flash" / "qspi_driver_new.v").write_text("module qspi; // conflict\nendmodule\n", encoding="utf-8")
    config = {
        "pilot_repository": str(pilot),
        "read_scope": {"paths": ["common/rtl/qspi_flash"]},
        "candidate_write_scope": {"paths": ["common/rtl/qspi_flash"]},
        "relevant_paths": ["common/rtl/qspi_flash/qspi_driver_new.v"],
    }
    bridge = BridgeProcess(tmp_path / "state", config)
    try:
        decision = bridge.request("guard_check", {"tool_name": "write", "paths": ["common/rtl/qspi_flash/qspi_driver_new.v"]})
        assert decision["allowed"] is False
        assert decision["code"] == "WORKSPACE_CONFLICTING"
    finally:
        bridge.stop()


def test_guard_allows_clean_workspace_outside_task_scope(tmp_path):
    pilot = make_pilot_repo(tmp_path)
    config = {
        "pilot_repository": str(pilot),
        "read_scope": {"paths": ["common/rtl/qspi_flash"]},
        "candidate_write_scope": {"paths": []},
        "relevant_paths": ["common/rtl/qspi_flash/qspi_driver_new.v"],
    }
    bridge = BridgeProcess(tmp_path / "state", config)
    try:
        decision = bridge.request("guard_check", {"tool_name": "write", "paths": ["common/rtl/qspi_flash/qspi_driver_new.v"]})
        # no active task -> allowed (task-scope governance not in effect)
        assert decision["allowed"] is True
    finally:
        bridge.stop()
