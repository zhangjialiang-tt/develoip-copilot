#!/usr/bin/env python3
"""Parse simulation log files and extract structured results with robust PASS/FAIL determination."""
import argparse
import re
import json
import sys
from pathlib import Path
from enum import Enum


class TestStatus(Enum):
    """Test result status with clear semantics."""
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    INCONSISTENT = "INCONSISTENT"


def parse_log(filepath: str) -> dict:
    """Parse a simulation log file for results, errors, and warnings.

    Returns a dict with the following structure:
    {
        "file": str,
        "status": TestStatus value,
        "pass": bool,  # Backward compatibility
        "errors": list[str],
        "warnings": list[str],
        "assertions": list[str],
        "summary": dict,
        "evidence": dict
    }
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")

    result = {
        "file": str(path),
        "status": TestStatus.UNKNOWN,
        "pass": False,  # Backward compatibility
        "errors": [],
        "warnings": [],
        "assertions": [],
        "summary": {},
        "evidence": {
            "explicit_test_result": None,
            "error_count": None,
            "assertion_failures": [],
            "fatal_errors": [],
            "explicit_failures": [],
            "explicit_passes": []
        }
    }

    for line in content.splitlines():
        stripped = line.strip()

        # Error patterns (excluding assertion failures which are handled separately)
        if re.match(r"^\s*\*\* Error", stripped, re.IGNORECASE):
            result["errors"].append(stripped)
            result["evidence"]["explicit_failures"].append(stripped)

            # Check for fatal errors
            if re.search(r"\bfatal\b", stripped, re.IGNORECASE):
                result["evidence"]["fatal_errors"].append(stripped)

        elif re.search(r"\bERROR\b", stripped, re.IGNORECASE) and "Error:" in stripped:
            result["errors"].append(stripped)
            result["evidence"]["explicit_failures"].append(stripped)

        # Warning patterns
        if re.match(r"^\s*\*\* Warning", stripped, re.IGNORECASE):
            result["warnings"].append(stripped)
        elif re.search(r"\bWARNING\b", stripped, re.IGNORECASE) and "Warning:" in stripped:
            result["warnings"].append(stripped)

        # Assertion failure patterns
        if re.search(r"(assertion|assert).*fail", stripped, re.IGNORECASE):
            result["assertions"].append(stripped)
            result["evidence"]["assertion_failures"].append(stripped)

        # Explicit test result patterns
        if re.search(r"(TEST|test)\s*(PASSED|passed)\b", stripped):
            result["summary"]["test_result"] = "PASSED"
            result["evidence"]["explicit_passes"].append(stripped)
            result["evidence"]["explicit_test_result"] = "PASSED"
        elif re.search(r"(TEST|test)\s*(FAILED|failed)\b", stripped):
            result["summary"]["test_result"] = "FAILED"
            result["evidence"]["explicit_test_result"] = "FAILED"

        # Error count patterns
        m = re.search(r"Errors?\s*:\s*(\d+)", stripped, re.IGNORECASE)
        if m:
            result["summary"]["error_count"] = int(m.group(1))
            result["evidence"]["error_count"] = int(m.group(1))

        # Warning count patterns
        m = re.search(r"Warnings?\s*:\s*(\d+)", stripped, re.IGNORECASE)
        if m:
            result["summary"]["warning_count"] = int(m.group(1))

    # Determine status using multi-layer logic
    result["status"] = _determine_status(result["evidence"])

    # Set backward compatibility field
    result["pass"] = (result["status"] == TestStatus.PASS)

    return result


def _determine_status(evidence: dict) -> TestStatus:
    """Determine test status using multi-layer logic.

    Priority order:
    1. Evidence conflict (e.g., assertion failure + zero error count) → INCONSISTENT
    2. Assertion failures → FAIL
    3. Fatal errors → FAIL
    4. Explicit TEST FAILED → FAIL
    5. Explicit TEST PASSED + no failure evidence → PASS
    6. Zero error count + no failure evidence → PASS
    7. Otherwise → UNKNOWN
    """
    # Check for evidence conflict FIRST
    has_failure_evidence = (
        evidence["assertion_failures"] or
        evidence["fatal_errors"] or
        evidence["explicit_failures"] or
        evidence["explicit_test_result"] == "FAILED"
    )

    has_pass_evidence = (
        evidence["explicit_test_result"] == "PASSED" or
        (evidence["error_count"] is not None and evidence["error_count"] == 0)
    )

    if has_failure_evidence and has_pass_evidence:
        return TestStatus.INCONSISTENT

    # Check for definitive failure evidence
    if evidence["assertion_failures"]:
        return TestStatus.FAIL

    if evidence["fatal_errors"]:
        return TestStatus.FAIL

    if evidence["explicit_test_result"] == "FAILED":
        return TestStatus.FAIL

    # Check for definitive pass evidence
    if evidence["explicit_test_result"] == "PASSED" and not has_failure_evidence:
        return TestStatus.PASS

    if evidence["error_count"] is not None and evidence["error_count"] == 0 and not has_failure_evidence:
        return TestStatus.PASS

    # Default to UNKNOWN
    return TestStatus.UNKNOWN


def main():
    parser = argparse.ArgumentParser(description="Parse simulation log files with robust status determination")
    parser.add_argument("logfiles", nargs="+", help="Simulation log files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    all_results = []
    for f in args.logfiles:
        result = parse_log(f)
        # Convert Enum to string for JSON serialization
        result["status"] = result["status"].value
        all_results.append(result)

    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        for r in all_results:
            print(f"\nFile: {r['file']}")
            print(f"  Status: {r['status']}")
            if r["summary"]:
                print(f"  Summary: {r['summary']}")
            if r["errors"]:
                print(f"  Errors ({len(r['errors'])}):")
                for e in r["errors"][:5]:
                    print(f"    {e}")
                if len(r["errors"]) > 5:
                    print(f"    ... and {len(r['errors']) - 5} more")
            if r["warnings"]:
                print(f"  Warnings ({len(r['warnings'])}):")
                for w in r["warnings"][:3]:
                    print(f"    {w}")
                if len(r["warnings"]) > 3:
                    print(f"    ... and {len(r['warnings']) - 3} more")
            if r["assertions"]:
                print(f"  Assertion failures ({len(r['assertions'])}):")
                for a in r["assertions"]:
                    print(f"    {a}")
            if r["status"] == "INCONSISTENT":
                print(f"  ⚠️  Evidence conflict detected:")
                ev = r["evidence"]
                if ev["assertion_failures"]:
                    print(f"     - Found {len(ev['assertion_failures'])} assertion failure(s)")
                if ev["explicit_test_result"] == "PASSED":
                    print(f"     - But explicit result is PASSED")
                if ev["error_count"] == 0:
                    print(f"     - But error count is 0")


if __name__ == "__main__":
    main()