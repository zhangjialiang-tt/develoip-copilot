#!/usr/bin/env python3
"""Extract port and parameter interfaces from Verilog/SystemVerilog modules."""
import argparse
import re
import json
import sys
from pathlib import Path

KEYWORDS = {
    "wire", "reg", "logic", "bit", "signed", "input", "output", "inout",
    "parameter", "localparam", "typedef", "enum", "struct", "generate",
    "function", "task", "module", "endmodule",
}


def _strip_comments(content: str) -> str:
    content = re.sub(r"//.*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    # drop `include / `define lines (not parsed here)
    content = re.sub(r"`\w+.*", "", content)
    return content


def _balanced(text: str, start: int):
    """text[start] must be '('; return (inner_text, index_after_close)."""
    assert text[start] == "("
    depth = 0
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    return text[start + 1:], n


def _parse_header(content: str, i: int):
    """Starting right after 'module NAME', consume #(...) and (...).
    Returns (param_block, port_block, index_after_close)."""
    param_block = ""
    port_block = ""
    n = len(content)
    # skip spaces
    while i < n and content[i] in " \t\r\n":
        i += 1
    if i < n and content[i] == "#":
        i += 1
        while i < n and content[i] in " \t\r\n":
            i += 1
        if i < n and content[i] == "(":
            param_block, i = _balanced(content, i)
    while i < n and content[i] in " \t\r\n":
        i += 1
    if i < n and content[i] == "(":
        port_block, i = _balanced(content, i)
    return param_block, port_block, i


def _find_modules(content: str):
    """Return list of dicts: name, line, param_block, port_block, body."""
    modules = []
    for m in re.finditer(r"\bmodule\s+(\w+)", content):
        name = m.group(1)
        line = content[: m.start()].count("\n") + 1
        param_block, port_block, i = _parse_header(content, m.end())
        end = content.find("endmodule", i)
        body = content[i:end] if end != -1 else content[i:]
        modules.append({
            "name": name, "line": line,
            "param_block": param_block, "port_block": port_block, "body": body,
        })
    return modules


def extract_interfaces(filepath: str) -> list[dict]:
    """Extract port and parameter definitions from a Verilog/SystemVerilog file."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    interfaces = []

    # Inline port parse: capture direction, optional width right after the type,
    # and the name. Width is parsed at the declaration site (no global search),
    # so a 1-bit port keeps width=None instead of a mis-matched range.
    port_re = re.compile(
        r"\b(input|output|inout)\b\s*"
        r"(?:wire|reg|logic|bit|signed)?\s*"
        r"(?:\[(?P<w>[^\]]+)\])?\s*"
        r"(?P<name>\w+)"
    )
    # Parameter default may contain parentheses (e.g. $clog2(WIDTH)).
    param_re = re.compile(
        r"\bparameter\s+(?:\[(?P<pw>[^\]]+)\]\s*)?(?P<pname>\w+)\s*=\s*(?P<pval>[^,;]+)"
    )

    for mod in _find_modules(content):
        params = []
        for pm in param_re.finditer(mod["param_block"] + "\n" + mod["body"]):
            params.append({
                "name": pm.group("pname"),
                "default": pm.group("pval").strip(),
                "width": pm.group("pw"),
            })

        ports = []
        for pm in port_re.finditer(mod["port_block"] + "\n" + mod["body"]):
            direction = pm.group(1)
            name = pm.group("name")
            if name in KEYWORDS:
                continue
            width = pm.group("w")  # None => implicit 1-bit
            ports.append({
                "name": name,
                "direction": direction,
                "width": width,
            })

        interfaces.append({
            "module": mod["name"],
            "file": str(path),
            "line": mod["line"],
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
                    w = f"[{p['width']}] " if p["width"] else ""
                    print(f"    {p['name']} = {p['default']} {w}")
            if iface["ports"]:
                print("  Ports:")
                for port in iface["ports"]:
                    w = port["width"] if port["width"] else "1-bit"
                    print(f"    {port['direction']:6s} {w:12s} {port['name']}")


if __name__ == "__main__":
    main()
