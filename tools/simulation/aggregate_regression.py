#!/usr/bin/env python3
"""Aggregate regression test results from multiple simulation logs."""
import argparse
import json
import sys
from pathlib import Path

# Reuse parse_log logic
sys.path.insert(0, str(Path(__file__).parent))
from parse_log import parse_log


def aggregate_regression(log_files: list[str]) -> dict:
    """Aggregate results from multiple regression test logs."""
    total = len(log_files)
    passed = 0
    failed = 0
    results = []

    for f in log_files:
        result = parse_log(f)
        if result["pass"]:
            passed += 1
        else:
            failed += 1
        results.append({
            "file": result["file"],
            "pass": result["pass"],
            "errors": len(result["errors"]),
            "warnings": len(result["warnings"]),
        })

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "details": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Aggregate regression test results")
    parser.add_argument("logfiles", nargs="+", help="Simulation log files from regression")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    summary = aggregate_regression(args.logfiles)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Regression Summary: {summary['passed']}/{summary['total']} PASSED")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        if summary["failed"] > 0:
            print("\nFailed tests:")
            for d in summary["details"]:
                if not d["pass"]:
                    print(f"  {d['file']} ({d['errors']} errors, {d['warnings']} warnings)")


if __name__ == "__main__":
    main()
