#!/usr/bin/env python3
"""Parse simulation log files and extract structured results."""
import argparse
import re
import json
import sys
from pathlib import Path


def parse_log(filepath: str) -> dict:
    """Parse a simulation log file for results, errors, and warnings."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")

    result = {
        "file": str(path),
        "errors": [],
        "warnings": [],
        "assertions": [],
        "summary": {},
        "pass": False,
    }

    for line in content.splitlines():
        stripped = line.strip()

        # Error patterns
        if re.match(r"^\s*\*\* Error", stripped, re.IGNORECASE):
            result["errors"].append(stripped)
        elif re.search(r"\bERROR\b", stripped, re.IGNORECASE) and "Error:" in stripped:
            result["errors"].append(stripped)

        # Warning patterns
        if re.match(r"^\s*\*\* Warning", stripped, re.IGNORECASE):
            result["warnings"].append(stripped)
        elif re.search(r"\bWARNING\b", stripped, re.IGNORECASE) and "Warning:" in stripped:
            result["warnings"].append(stripped)

        # Assertion failure
        if re.search(r"(assertion|ASSERT).*fail", stripped, re.IGNORECASE):
            result["assertions"].append(stripped)

        # Summary patterns
        if re.search(r"(TEST|test)\s*(PASSED|passed)", stripped):
            result["summary"]["test_result"] = "PASSED"
            result["pass"] = True
        elif re.search(r"(TEST|test)\s*(FAILED|failed)", stripped):
            result["summary"]["test_result"] = "FAILED"
            result["pass"] = False

        # Error count
        m = re.search(r"Errors?\s*:\s*(\d+)", stripped, re.IGNORECASE)
        if m:
            result["summary"]["error_count"] = int(m.group(1))

        # Warning count
        m = re.search(r"Warnings?\s*:\s*(\d+)", stripped, re.IGNORECASE)
        if m:
            result["summary"]["warning_count"] = int(m.group(1))

    # If we found explicit error counts, use them
    if "error_count" in result["summary"]:
        result["pass"] = result["summary"]["error_count"] == 0

    return result


def main():
    parser = argparse.ArgumentParser(description="Parse simulation log files")
    parser.add_argument("logfiles", nargs="+", help="Simulation log files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    all_results = []
    for f in args.logfiles:
        all_results.append(parse_log(f))

    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        for r in all_results:
            print(f"\nFile: {r['file']}")
            status = "PASS" if r["pass"] else "FAIL"
            print(f"  Result: {status}")
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
            if r["assertions"]:
                print(f"  Assertion failures ({len(r['assertions'])}):")
                for a in r["assertions"]:
                    print(f"    {a}")


if __name__ == "__main__":
    main()
