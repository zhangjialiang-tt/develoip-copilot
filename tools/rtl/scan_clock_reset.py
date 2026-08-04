#!/usr/bin/env python3
"""Scan clock and reset signals in Verilog/SystemVerilog files."""
import argparse
import re
import json
import sys
from pathlib import Path

RESET_NAME_RE = re.compile(r"rst|reset", re.IGNORECASE)
CLOCK_NAME_RE = re.compile(r"clk|clock|\bck\b", re.IGNORECASE)


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
    """Return list of dicts: name, line, port_block, body."""
    modules = []
    for m in re.finditer(r"\bmodule\s+(\w+)", content):
        name = m.group(1)
        line = content[: m.start()].count("\n") + 1
        param_block, port_block, i = _parse_header(content, m.end())
        end = content.find("endmodule", i)
        body = content[i:end] if end != -1 else content[i:]
        modules.append({
            "name": name, "line": line,
            "port_block": port_block, "body": body,
        })
    return modules


def _is_reset_name(sig: str) -> bool:
    return bool(RESET_NAME_RE.search(sig))


def _is_clock_name(sig: str) -> bool:
    return bool(CLOCK_NAME_RE.search(sig)) and not _is_reset_name(sig)


def _active_low_from_name(sig: str) -> bool:
    return sig.lower().endswith(("_n", "_b", "_l", "_neg", "_bar"))


def _classify_reset_condition(cond: str):
    """Infer (active_low, signal) from an if-condition expression."""
    c = cond.strip()
    m = re.search(r"(\w+)\s*==\s*1'b0", c)
    if m:
        return True, m.group(1)
    m = re.search(r"(\w+)\s*===\s*1'b0", c)
    if m:
        return True, m.group(1)
    m = re.search(r"(\w+)\s*==\s*1'b1", c)
    if m:
        return False, m.group(1)
    m = re.search(r"(\w+)\s*===\s*1'b1", c)
    if m:
        return False, m.group(1)
    m = re.match(r"[!~]\s*(\w+)", c)
    if m:
        return True, m.group(1)
    m = re.match(r"(\w+)", c)
    if m and _is_reset_name(m.group(1)):
        return _active_low_from_name(m.group(1)), m.group(1)
    return None, None


def scan_clock_reset(filepath: str) -> list[dict]:
    """Scan for clock and reset signals in an RTL file.

    Returns per-module dicts with structured clock/reset details:
      clocks: [{signal, edge, type}]            type ∈ port|sensitivity|generated
      resets: [{signal, edge, active_low, sync, assertion}]
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    results = []

    sens_re = re.compile(r"\balways(?:_ff|_comb|_latch)?\s*@\s*\(([^)]*)\)")
    if_re = re.compile(r"\bif\s*\(([^)]*)\)")
    port_re = re.compile(
        r"\b(input|output)\b\s*(?:wire|reg|logic|bit)?\s*(?:\[[^\]]+\])?\s*(\w+)"
    )
    gen_re = re.compile(r"(\w+)\s*<=\s*~\s*(\w+)")

    for mod in _find_modules(content):
        scan_text = mod["port_block"] + "\n" + mod["body"]
        clocks = {}
        resets = {}

        def ensure_clock(sig, typ):
            c = clocks.setdefault(sig, {"signal": sig, "edge": "unknown", "type": typ})
            if typ == "sensitivity":
                c["type"] = "sensitivity"
            return c

        def ensure_reset(sig):
            return resets.setdefault(sig, {
                "signal": sig, "edge": "unknown",
                "active_low": _active_low_from_name(sig),
                "sync": None, "assertion": None,
            })

        # Port-declared clock/reset candidates (covers ANSI port lists).
        for pm in port_re.finditer(scan_text):
            sig = pm.group(2)
            if _is_clock_name(sig):
                ensure_clock(sig, "port")
            elif _is_reset_name(sig):
                ensure_reset(sig)

        # Sensitivity lists: clocks and async resets.
        for sm in sens_re.finditer(scan_text):
            events = re.split(r"\bor\b", sm.group(1))
            for ev in events:
                em = re.match(r"\s*(posedge|negedge)\s+(\w+)\s*", ev)
                if not em:
                    continue
                edge = "pos" if em.group(1) == "posedge" else "neg"
                sig = em.group(2)
                if _is_reset_name(sig):
                    r = ensure_reset(sig)
                    r["sync"] = False
                    r["edge"] = edge
                    if edge == "neg":
                        r["active_low"] = True
                elif _is_clock_name(sig):
                    c = ensure_clock(sig, "sensitivity")
                    c["edge"] = edge

        # if-based resets: sync unless already marked async.
        for im in if_re.finditer(scan_text):
            active_low, sig = _classify_reset_condition(im.group(1))
            if sig and _is_reset_name(sig):
                r = ensure_reset(sig)
                if r["sync"] is not False:
                    r["sync"] = True
                if active_low is not None:
                    r["active_low"] = active_low
                r["assertion"] = im.group(1).strip()

        # Generated-clock heuristic: reg <= ~known_clock (or self-toggle of a
        # clock-like signal). Conservative: only clock-named derived signals.
        known = set(clocks.keys())
        for gm in gen_re.finditer(scan_text):
            derived, src = gm.group(1), gm.group(2)
            if (src in known or derived == src) and _is_clock_name(derived):
                ensure_clock(derived, "generated")

        if clocks or resets:
            results.append({
                "module": mod["name"],
                "file": str(path),
                "line": mod["line"],
                "clocks": list(clocks.values()),
                "resets": list(resets.values()),
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
                print("  Clocks:")
                for c in r["clocks"]:
                    print(f"    {c['signal']:12s} edge={c['edge']:6s} type={c['type']}")
            if r["resets"]:
                print("  Resets:")
                for rst in r["resets"]:
                    al = "low" if rst["active_low"] else "high"
                    syn = rst["sync"]
                    syn_s = "async" if syn is False else ("sync" if syn else "unknown")
                    print(f"    {rst['signal']:12s} active={al:5s} {syn_s}")


if __name__ == "__main__":
    main()
