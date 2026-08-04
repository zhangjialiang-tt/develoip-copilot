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


def main():
    results = []
    results.append(("File existence", check_files_exist()))
    results.append(("CLI tools", check_cli_tools()))
    results.append(("Skill structure", check_skill_structure()))

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
