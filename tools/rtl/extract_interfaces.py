#!/usr/bin/env python3
"""Extract port and parameter interfaces from Verilog/SystemVerilog modules."""
import argparse
import re
import json
import sys
from pathlib import Path


def extract_interfaces(filepath: str) -> list[dict]:
    """Extract port and parameter definitions from a Verilog/SystemVerilog file."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")
    content = re.sub(r"//.*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

    interfaces = []

    # Match module ... endmodule blocks
    module_pattern = re.compile(
        r"\bmodule\s+(\w+)\s*(?:#\s*\((.*?)\))?\s*(?:\((.*?)\))?\s*;(.*?)endmodule",
        re.DOTALL,
    )

    for match in module_pattern.finditer(content):
        module_name = match.group(1)
        param_block = match.group(2) or ""
        port_block = match.group(3) or ""
        body = match.group(4) or ""

        # Extract parameters
        params = []
        for pm in re.finditer(
            r"parameter\s+(?:\[.*?\]\s+)?(\w+)\s*=\s*([^,;)]+)", param_block
        ):
            params.append({"name": pm.group(1), "default": pm.group(2).strip()})

        # Also check body for parameter overrides
        if not params:
            for pm in re.finditer(
                r"parameter\s+(?:\[.*?\]\s+)?(\w+)\s*=\s*([^;]+)", body
            ):
                params.append({"name": pm.group(1), "default": pm.group(2).strip()})

        # Extract ports (Verilog-2001 style: input/output in port list)
        ports = []
        port_pattern = re.compile(
            r"(input|output|inout)\s+(?:wire|reg|logic)?\s*(?:\[[^\]]+\])?\s*(\w+)"
        )
        for port_match in port_pattern.finditer(port_block + "\n" + body):
            direction = port_match.group(1)
            name = port_match.group(2)
            # Skip if name looks like a keyword
            if name in ("wire", "reg", "logic", "input", "output", "inout"):
                continue
            # Try to extract width from surrounding context
            width_match = re.search(
                r"\[[^\]]+\]\s*" + re.escape(name),
                port_block + "\n" + body,
            )
            if width_match:
                width = width_match.group(0).split("]")[0] + "]"
                width = width.strip()
            else:
                width = "[0:0]"
            ports.append({"name": name, "direction": direction, "width": width})

        interfaces.append({
            "module": module_name,
            "file": str(path),
            "line": content[: match.start()].count("\n") + 1,
            "parameters": params,
            "ports": ports,
        })

    return interfaces


def main():
    parser = argparse.ArgumentParser(description="Extract port and parameter interfaces")
    parser.add_argument("files", nargs="+", help="Verilog/SystemVerilog files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--module", help="Filter by module name")
    args = parser.parse_args()

    all_interfaces = []
    for f in args.files:
        all_interfaces.extend(extract_interfaces(f))

    if args.module:
        all_interfaces = [i for i in all_interfaces if i["module"] == args.module]

    if args.json:
        print(json.dumps(all_interfaces, indent=2))
    else:
        for iface in all_interfaces:
            print(f"\nModule: {iface['module']} ({iface['file']}:{iface['line']})")
            if iface["parameters"]:
                print("  Parameters:")
                for p in iface["parameters"]:
                    print(f"    {p['name']} = {p['default']}")
            if iface["ports"]:
                print("  Ports:")
                for port in iface["ports"]:
                    print(f"    {port['direction']:6s} {port['width']:10s} {port['name']}")


if __name__ == "__main__":
    main()
