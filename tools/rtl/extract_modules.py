#!/usr/bin/env python3
"""Extract module definitions from Verilog/SystemVerilog files."""
import argparse
import re
import json
import sys
from pathlib import Path


def extract_modules(filepath: str) -> list[dict]:
    """Extract module definitions from a Verilog/SystemVerilog file."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")

    # Remove single-line and multi-line comments
    content = re.sub(r"//.*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

    modules = []
    # Match: module <name> #(param) (port_list);
    pattern = re.compile(
        r"\bmodule\s+(\w+)\s*(?:#\s*\([^)]*\))?\s*(?:\([^)]*\))?\s*;",
        re.MULTILINE,
    )
    for match in pattern.finditer(content):
        modules.append({
            "name": match.group(1),
            "file": str(path),
            "line": content[: match.start()].count("\n") + 1,
        })

    return modules


def main():
    parser = argparse.ArgumentParser(description="Extract module definitions from RTL files")
    parser.add_argument("files", nargs="+", help="Verilog/SystemVerilog files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    all_modules = []
    for f in args.files:
        all_modules.extend(extract_modules(f))

    if args.json:
        print(json.dumps(all_modules, indent=2))
    else:
        for m in all_modules:
            print(f"{m['name']:30s} {m['file']}:{m['line']}")


if __name__ == "__main__":
    main()
