#!/usr/bin/env python3
"""Smoke test: verify OMP can discover Skills and invoke Agents.

This test validates:
1. Skill files exist in .omp/skills/*/SKILL.md
2. Agent files exist in .omp/agents/*.md
3. Python CLI tools can run independently
4. CLI tools return proper exit codes
5. CLI tools produce expected output format
"""
import subprocess
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SKILLS = [
    ".omp/skills/rtl-architecture-analysis/SKILL.md",
    ".omp/skills/rtl-to-testbench/SKILL.md",
    ".omp/skills/simulation-analysis/SKILL.md",
]

AGENTS = [
    ".omp/agents/rtl-analyst.md",
    ".omp/agents/verification-engineer.md",
    ".omp/agents/simulation-analyst.md",
]

CLI_TOOLS = [
    ("python tools/rtl/extract_modules.py --help", "RTL module extractor"),
    ("python tools/rtl/extract_interfaces.py --help", "RTL interface extractor"),
    ("python tools/rtl/build_hierarchy.py --help", "RTL hierarchy builder"),
    ("python tools/rtl/scan_clock_reset.py --help", "Clock/reset scanner"),
    ("python tools/simulation/parse_log.py --help", "Log parser"),
    ("python tools/simulation/extract_failures.py --help", "Failure extractor"),
    ("python tools/simulation/aggregate_regression.py --help", "Regression aggregator"),
    ("python tools/simulation/run.py --help", "Simulation runner"),
]


def check_files_exist():
    """Verify all expected files exist."""
    print("=== File Existence Check ===")
    all_ok = True

    for skill in SKILLS:
        path = REPO_ROOT / skill
        exists = path.exists()
        status = "PASS" if exists else "FAIL"
        print(f"  [{status}] {skill}")
        if not exists:
            all_ok = False

    for agent in AGENTS:
        path = REPO_ROOT / agent
        exists = path.exists()
        status = "PASS" if exists else "FAIL"
        print(f"  [{status}] {agent}")
        if not exists:
            all_ok = False

    return all_ok


def check_cli_tools():
    """Verify CLI tools can execute and show help."""
    print("\n=== CLI Tool Check ===")
    all_ok = True

    for cmd, desc in CLI_TOOLS:
        try:
            result = subprocess.run(
                cmd.split(),
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                print(f"  [PASS] {desc}: {cmd}")
            else:
                print(f"  [FAIL] {desc}: returncode={result.returncode}")
                if result.stderr:
                    print(f"         stderr: {result.stderr.strip()[:100]}")
                all_ok = False
        except FileNotFoundError as e:
            print(f"  [FAIL] {desc}: {e}")
            all_ok = False
        except subprocess.TimeoutExpired:
            print(f"  [FAIL] {desc}: timed out")
            all_ok = False

    return all_ok


def check_skill_structure():
    """Verify SKILL.md files have required sections."""
    print("\n=== Skill Structure Check ===")
    required_sections = [
        "When to use",
        "Do not use",
        "Required inputs",
        "Procedure",
        "Delegation",
        "Tools",
        "Outputs",
        "Validation",
        "Failure handling",
        "Safety",
    ]
    all_ok = True

    for skill_path in SKILLS:
        path = REPO_ROOT / skill_path
        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8")
        missing = [s for s in required_sections if s not in content]

        if missing:
            print(f"  [FAIL] {skill_path}: missing sections: {missing}")
            all_ok = False
        else:
            print(f"  [PASS] {skill_path}: all required sections present")

    return all_ok


def check_tool_real_output():
    """Verify the four RTL tools actually run on a normal fixture and emit valid JSON."""
    print("\n=== RTL Tool Real Output Check ===")
    fixture = REPO_ROOT / "fixtures" / "rtl" / "normal" / "counter.v"
    if not fixture.exists():
        print("  [FAIL] fixture missing: fixtures/rtl/normal/counter.v")
        return False
    cases = [
        ("extract_modules", "name"),
        ("extract_interfaces", "module"),
        ("build_hierarchy", "module"),
        ("scan_clock_reset", "module"),
    ]
    all_ok = True
    for tool, key in cases:
        try:
            result = subprocess.run(
                ["python", f"tools/rtl/{tool}.py", "--json", str(fixture)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            print(f"  [FAIL] {tool}: timed out")
            all_ok = False
            continue
        if result.returncode != 0:
            print(f"  [FAIL] {tool}: returncode={result.returncode}")
            all_ok = False
            continue
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"  [FAIL] {tool}: stdout not valid JSON: {e}")
            all_ok = False
            continue
        if not isinstance(data, list) or len(data) == 0:
            print(f"  [FAIL] {tool}: empty or non-list output")
            all_ok = False
            continue
        if key not in data[0]:
            print(f"  [FAIL] {tool}: missing key '{key}' in first record")
            all_ok = False
            continue
        print(f"  [PASS] {tool}: valid JSON, {len(data)} module(s), key '{key}' present")
    return all_ok


def check_simulation_tools_output():
    """Verify the simulation tools (downstream of rtl-to-testbench) actually run and emit valid JSON."""
    print("\n=== Simulation Tool Real Output Check ===")
    sim_pass = REPO_ROOT / "fixtures" / "simulation" / "normal" / "sim_pass.log"
    sim_fail = REPO_ROOT / "fixtures" / "simulation" / "error" / "sim_fail.log"
    if not sim_pass.exists():
        print(f"  [FAIL] fixture missing: {sim_pass}")
        return False
    if not sim_fail.exists():
        print(f"  [FAIL] fixture missing: {sim_fail}")
        return False

    all_ok = True

    # parse_log on a PASSING log -> pass == True
    try:
        r = subprocess.run(
            ["python", "tools/simulation/parse_log.py", str(sim_pass), "--json"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("  [FAIL] parse_log (pass): timed out")
        return False
    if r.returncode != 0:
        print(f"  [FAIL] parse_log (pass): returncode={r.returncode} stderr={r.stderr[:120]}")
        return False
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        print(f"  [FAIL] parse_log (pass): stdout not valid JSON: {e}")
        return False
    if not isinstance(data, list) or not data or data[0].get("pass") is not True:
        print("  [FAIL] parse_log (pass): expected list with first record pass==True")
        all_ok = False
    else:
        print("  [PASS] parse_log (pass): valid JSON, first record pass==True")

    # extract_failures (first-only) on a PASSING log -> empty list
    try:
        r = subprocess.run(
            ["python", "tools/simulation/extract_failures.py", str(sim_pass), "--first-only", "--json"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("  [FAIL] extract_failures (pass): timed out")
        return False
    if r.returncode != 0:
        print(f"  [FAIL] extract_failures (pass): returncode={r.returncode}")
        return False
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        print(f"  [FAIL] extract_failures (pass): stdout not valid JSON: {e}")
        return False
    if data != []:
        print(f"  [FAIL] extract_failures (pass): expected [] for passing log, got {data}")
        all_ok = False
    else:
        print("  [PASS] extract_failures (pass): valid JSON, empty list for passing log")

    # parse_log on a FAILING log -> pass == False
    try:
        r = subprocess.run(
            ["python", "tools/simulation/parse_log.py", str(sim_fail), "--json"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("  [FAIL] parse_log (fail): timed out")
        return False
    if r.returncode != 0:
        print(f"  [FAIL] parse_log (fail): returncode={r.returncode}")
        return False
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        print(f"  [FAIL] parse_log (fail): stdout not valid JSON: {e}")
        return False
    if not isinstance(data, list) or not data or data[0].get("pass") is not False:
        print("  [FAIL] parse_log (fail): expected list with first record pass==False")
        all_ok = False
    else:
        print("  [PASS] parse_log (fail): valid JSON, first record pass==False")

    return all_ok


def check_regression_aggregation():
    """Verify aggregate_regression.py actually runs on normal+error logs and emits valid JSON."""
    print("\n=== Regression Aggregation Check ===")
    sim_pass = REPO_ROOT / "fixtures" / "simulation" / "normal" / "sim_pass.log"
    sim_fail = REPO_ROOT / "fixtures" / "simulation" / "error" / "sim_fail.log"
    if not sim_pass.exists() or not sim_fail.exists():
        print("  [FAIL] fixture missing for regression aggregation")
        return False
    try:
        r = subprocess.run(
            ["python", "tools/simulation/aggregate_regression.py", str(sim_pass), str(sim_fail), "--json"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("  [FAIL] aggregate_regression: timed out")
        return False
    if r.returncode != 0:
        print(f"  [FAIL] aggregate_regression: returncode={r.returncode} stderr={r.stderr[:160]}")
        return False
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        print(f"  [FAIL] aggregate_regression: stdout not valid JSON: {e}")
        return False
    if not isinstance(data, dict) or data.get("total") != 2 or data.get("passed") != 1 or data.get("failed") != 1:
        print(f"  [FAIL] aggregate_regression: expected total=2 passed=1 failed=1, got {data}")
        return False
    details = data.get("details", [])
    if not isinstance(details, list) or len(details) != 2:
        print(f"  [FAIL] aggregate_regression: expected 2 details, got {details}")
        return False
    print("  [PASS] aggregate_regression: valid JSON, total=2 passed=1 failed=1, details=2")
    return True


def main():
    results = []
    results.append(("File existence", check_files_exist()))
    results.append(("CLI tools", check_cli_tools()))
    results.append(("Skill structure", check_skill_structure()))
    results.append(("RTL tool real output", check_tool_real_output()))
    results.append(("Simulation tool real output", check_simulation_tools_output()))
    results.append(("Regression aggregation", check_regression_aggregation()))

    print("\n=== Summary ===")
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_pass = False

    if all_pass:
        print("\nAll smoke tests PASSED.")
        sys.exit(0)
    else:
        print("\nSome smoke tests FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
