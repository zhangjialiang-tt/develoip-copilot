#!/usr/bin/env python3
"""Build module instantiation hierarchy from Verilog/SystemVerilog files."""
import argparse
import re
import json
import sys
from pathlib import Path

KEYWORDS = {
    "if", "else", "case", "begin", "end", "always", "initial",
    "assign", "generate", "for", "while", "function", "task",
    "input", "output", "inout", "wire", "reg", "logic",
    "parameter", "localparam", "typedef", "enum", "struct", "module",
}
PRIMITIVES = {
    "and", "or", "not", "buf", "bufif0", "bufif1", "notif0", "notif1",
    "nand", "nor", "xor", "xnor", "cmos", "rcmos", "tran", "tranif0",
    "tranif1", "rtran", "rtranif0", "rtranif1", "pullup", "pulldown",
}


def _strip_comments(content: str) -> str:
    content = re.sub(r"//.*", "", content)
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = re.sub(r"`\w+.*", "", content)
    return content


def _balanced(text: str, start: int):
    """text[start] must be '('; return (inner_text, index_after_close)."""
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
    """Return list of dicts: name, line, body."""
    modules = []
    for m in re.finditer(r"\bmodule\s+(\w+)", content):
        name = m.group(1)
        line = content[: m.start()].count("\n") + 1
        _, _, i = _parse_header(content, m.end())
        end = content.find("endmodule", i)
        body = content[i:end] if end != -1 else content[i:]
        modules.append({"name": name, "line": line, "body": body})
    return modules


def _strip_param_overrides(text: str) -> str:
    """Remove `#(...)` blocks (balanced) so they don't interfere with the
    instantiation regex (e.g. parameter overrides with nested parens)."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "#" and i + 1 < n and text[i + 1] == "(":
            _, i = _balanced(text, i + 1)
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


# Strict instantiation: MODNAME <space> INSTANCE <(. MODNAME must be a real
# module (present in the cross-file map) and not a keyword/primitive, which
# excludes function/task calls, generate/for keywords, and gate primitives.
INST_RE = re.compile(r"\b(\w+)\s+(\w+)\s*\(")


def build_hierarchy(files) -> list[dict]:
    """Build instance hierarchy across all provided files.

    Returns a list of per-module dicts with children resolved to their
    defining file when that module is found among the inputs.
    """
    file_list = [str(Path(f)) for f in files]

    # Pass 1: build a global module -> file map (first occurrence wins).
    module_map = {}
    raw = {}
    for f in file_list:
        p = Path(f)
        if not p.exists():
            print(f"Error: file not found: {f}", file=sys.stderr)
            sys.exit(1)
        content = _strip_comments(p.read_text(encoding="utf-8", errors="replace"))
        raw[f] = content
        for mod in _find_modules(content):
            if mod["name"] not in module_map:
                module_map[mod["name"]] = f

    # Pass 2: resolve children with the global map.
    hierarchy = []
    for f in file_list:
        content = _strip_param_overrides(raw[f])
        for mod in _find_modules(content):
            children = []
            seen = set()
            for im in INST_RE.finditer(mod["body"]):
                modname = im.group(1)
                inst = im.group(2)
                if modname in KEYWORDS or modname in PRIMITIVES:
                    continue
                if modname == mod["name"]:
                    continue
                key = (modname, inst)
                if key in seen:
                    continue
                seen.add(key)
                child_file = module_map.get(modname, "未解析")
                children.append({
                    "module": modname,
                    "instance": inst,
                    "file": child_file,
                })
            hierarchy.append({
                "module": mod["name"],
                "file": f,
                "line": mod["line"],
                "children": children,
            })

    return hierarchy


def main():
    parser = argparse.ArgumentParser(description="Build module instantiation hierarchy")
    parser.add_argument("files", nargs="+", help="Verilog/SystemVerilog files")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--top", help="Show only hierarchy under this top module")
    args = parser.parse_args()

    all_hierarchy = build_hierarchy(args.files)

    if args.top:
        all_hierarchy = [h for h in all_hierarchy if h["module"] == args.top]

    if args.json:
        print(json.dumps(all_hierarchy, indent=2))
    else:
        for h in all_hierarchy:
            print(f"\nModule: {h['module']} ({h['file']}:{h['line']})")
            if h["children"]:
                for child in h["children"]:
                    loc = child["file"] if child["file"] != "未解析" else "未解析"
                    print(f"  -> {child['module']} ({child['instance']}) [{loc}]")
            else:
                print("  (leaf module)")


if __name__ == "__main__":
    main()
