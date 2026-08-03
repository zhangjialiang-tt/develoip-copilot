import json
import subprocess
import sys
from pathlib import Path


FIXTURE = Path(__file__).parents[1] / "fixtures" / "qspi-concat" / "qspi_fixture.py"


def run_fixture(baseline: str) -> dict:
    completed = subprocess.run([sys.executable, str(FIXTURE), "--baseline", baseline], check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def test_qspi_baseline_a_reproduces_known_failure():
    result = run_fixture("A")
    assert result["passed"] is False
    assert result["actual"] != result["expected"]


def test_qspi_baseline_b_passes_two_independent_checks():
    result = run_fixture("B")
    assert result["passed"] is True
    assert result["independent_check_passed"] is True
    assert result["actual"] == result["reference"] == result["expected"]
