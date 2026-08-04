#!/usr/bin/env python3
"""Scan clock and reset signals in Verilog/SystemVerilog files."""
import argparse
import re
import json
import sys
from pathlib import Path


def scan_clock_reset(filepath: str) -> list[dict]:
    """Scan for clock and reset signals in RTL files."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")
    content = re.sub(r"//.*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

    results = []

    module_pattern = re.compile(
        r"\bmodule\s+(\w+)\s*(?:#?\s*\([^)]*\))?\s*(?:\([^)]*\))?\s*;(.*?)endmodule",
        re.DOTALL,
    )

    # Clock signal patterns
    clock_patterns = [
        re.compile(r"\b(input|output)\s+(?:wire|reg|logic)?\s*(?:\[.*?\]\s+)?(clk\w*|clock\w*|CK\w*|CLK\w*)\b", re.IGNORECASE),
        re.compile(r"\balways\s*@\(\s*(?:posedge|negedge)\s+(\w+)", re.IGNORECASE),
    ]

    # Reset signal patterns
    reset_patterns = [
        re.compile(r"\b(input|output)\s+(?:wire|reg|logic)?\s*(?:\[.*?\]\s+)?(rst\w*|reset\w*|RST\w*|RESET\w*)\b", re.IGNORECASE),
        re.compile(r"\bif\s*\(\s*!?\s*(\w*(?:rst|reset)\w*)\s*\)", re.IGNORECASE),
    ]

    for match in module_pattern.finditer(content):
        module_name = match.group(1)
        body = match.group(2)

        clocks = set()
        resets = set()

        for pat in clock_patterns:
            for pm in pat.finditer(body):
                sig_name = pm.group(pm.lastindex)
                if sig_name.lower() not in ("input", "output", "wire", "reg", "logic"):
                    clocks.add(sig_name)

        for pat in reset_patterns:
            for pm in pat.finditer(body):
                sig_name = pm.group(pm.lastindex)
                if sig_name.lower() not in ("input", "output", "wire", "reg", "logic"):
                    resets.add(sig_name)

        if clocks or resets:
            results.append({
                "module": module_name,
                "file": str(path),
                "line": content[: match.start()].count("\n") + 1,
                "clocks": sorted(clocks),
                "resets": sorted(resets),
            })

    return results


def main():
    parser = argparse.ArgumentParser(description="Scan clock and reset signals")
    parser.add_argument("files", nargs="+", help="Verilog/SystemVerilog files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    all_results = []
    for f in args.files:
        all_results.extend(scan_clock_reset(f))

    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        for r in all_results:
            print(f"\nModule: {r['module']} ({r['file']}:{r['line']})")
            if r["clocks"]:
                print(f"  Clocks: {', '.join(r['clocks'])}")
            if r["resets"]:
                print(f"  Resets: {', '.join(r['resets'])}")


if __name__ == "__main__":
    main()
