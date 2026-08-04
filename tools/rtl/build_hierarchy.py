#!/usr/bin/env python3
"""Build module instantiation hierarchy from Verilog/SystemVerilog files."""
import argparse
import re
import json
import sys
from pathlib import Path


def build_hierarchy(filepath: str) -> list[dict]:
    """Build module instantiation hierarchy from RTL files."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")
    content = re.sub(r"//.*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

    hierarchy = []

    # Find module definitions and their instantiations
    module_pattern = re.compile(
        r"\bmodule\s+(\w+)\s*(?:#?\s*\([^)]*\))?\s*(?:\([^)]*\))?\s*;(.*?)endmodule",
        re.DOTALL,
    )

    # Instantiation pattern: module_name #(params) instance_name (ports);
    inst_pattern = re.compile(
        r"\b(\w+)\s*(?:#\s*\([^)]*\))?\s+(\w+)\s*\("
    )

    # Known keywords that are not module instantiations
    keywords = {
        "if", "else", "case", "begin", "end", "always", "initial",
        "assign", "generate", "for", "while", "function", "task",
        "input", "output", "inout", "wire", "reg", "logic",
        "parameter", "localparam", "typedef", "enum", "struct",
    }

    for match in module_pattern.finditer(content):
        module_name = match.group(1)
        body = match.group(2)

        children = []
        for inst_match in inst_pattern.finditer(body):
            mod = inst_match.group(1)
            inst = inst_match.group(2)
            if mod not in keywords and mod != module_name:
                children.append({"module": mod, "instance": inst})

        hierarchy.append({
            "module": module_name,
            "file": str(path),
            "line": content[: match.start()].count("\n") + 1,
            "children": children,
        })

    return hierarchy


def main():
    parser = argparse.ArgumentParser(description="Build module instantiation hierarchy")
    parser.add_argument("files", nargs="+", help="Verilog/SystemVerilog files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--top", help="Show only hierarchy under this top module")
    args = parser.parse_args()

    all_hierarchy = []
    for f in args.files:
        all_hierarchy.extend(build_hierarchy(f))

    if args.top:
        all_hierarchy = [h for h in all_hierarchy if h["module"] == args.top]

    if args.json:
        print(json.dumps(all_hierarchy, indent=2))
    else:
        for h in all_hierarchy:
            print(f"\nModule: {h['module']} ({h['file']}:{h['line']})")
            if h["children"]:
                for child in h["children"]:
                    print(f"  -> {child['module']} ({child['instance']})")
            else:
                print("  (leaf module)")


if __name__ == "__main__":
    main()
