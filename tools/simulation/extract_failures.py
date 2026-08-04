#!/usr/bin/env python3
"""Extract failure details from simulation logs."""
import argparse
import re
import json
import sys
from pathlib import Path


def extract_failures(filepath: str) -> list[dict]:
    """Extract failure events from simulation log, ordered by time."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")
    failures = []

    for line in content.splitlines():
        stripped = line.strip()

        # Match assertion failures with various time formats
        m = re.search(
            r"(?:at\s+time\s+(\d+)\s*ns?|#\s*(\d+)\s*ns?|at\s+(\d+)\s*ns?|@(\d+))\s*[-:]?\s*(.*?(?:assert|ASSERT|fail|FAIL|mismatch).*)",
            stripped,
            re.IGNORECASE,
        )
        if m:
            time_val = m.group(1) or m.group(2) or m.group(3) or m.group(4)
            msg = m.group(5)
            failures.append({
                "time": time_val,
                "message": msg,
                "type": "assertion",
            })

        # Match ** Error lines
        m = re.search(r"\*\*\s*Error[:\s]+(.*)", stripped, re.IGNORECASE)
        if m:
            # Try to extract time from the line or nearby
            time_m = re.search(r"time\s+(\d+)\s*ns?|at\s+(\d+)\s*ns?", stripped, re.IGNORECASE)
            time_val = None
            if time_m:
                time_val = time_m.group(1) or time_m.group(2)
            failures.append({
                "time": time_val,
                "message": m.group(1).strip(),
                "type": "error",
            })

        # Match data mismatch lines
        if re.search(r"(mismatch|mismatch|FAIL)", stripped, re.IGNORECASE) and not stripped.startswith("#"):
            time_m = re.search(r"time\s+(\d+)\s*ns?", stripped, re.IGNORECASE)
            time_val = time_m.group(1) if time_m else None
            if not any(f["message"] == stripped for f in failures):
                failures.append({
                    "time": time_val,
                    "message": stripped,
                    "type": "error",
                })

    # Sort by time if available; entries without time go to end, preserve order
    failures.sort(key=lambda x: (0, int(x["time"])) if x["time"] else (1, 0))

    return failures


def main():
    parser = argparse.ArgumentParser(description="Extract failures from simulation log")
    parser.add_argument("logfile", help="Simulation log file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--first-only", action="store_true", help="Show only first failure")
    args = parser.parse_args()

    failures = extract_failures(args.logfile)

    if args.first_only:
        failures = failures[:1]

    if args.json:
        print(json.dumps(failures, indent=2))
    else:
        if not failures:
            print("No failures found.")
        else:
            print(f"Found {len(failures)} failure(s):")
            for f in failures:
                time_str = f"@{f['time']}ns" if f["time"] else "@unknown"
                print(f"  [{f['type']:9s}] {time_str}: {f['message']}")


if __name__ == "__main__":
    main()
