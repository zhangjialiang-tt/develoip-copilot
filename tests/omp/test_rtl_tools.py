#!/usr/bin/env python3
"""Tests for RTL analysis tools (extract_interfaces / build_hierarchy / scan_clock_reset).

These tests run the deterministic CLI tools on fixtures and assert the
behaviors fixed/added in P1:
- parameter defaults may contain parentheses (e.g. $clog2(WIDTH))
- port widths are parsed inline (no mis-matched range)
- hierarchy resolves child modules across files
- clock/reset scan covers always_ff, low-active resets, sync/async, generated clocks
"""
import sys
import os
import json
import subprocess
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RTL = os.path.join(REPO_ROOT, "tools", "rtl")
FIX = os.path.join(REPO_ROOT, "fixtures", "rtl")

sys.path.insert(0, RTL)

import extract_interfaces  # noqa: E402
import build_hierarchy     # noqa: E402
import scan_clock_reset    # noqa: E402


def _first(lst, **attrs):
    for item in lst:
        if all(item.get(k) == v for k, v in attrs.items()):
            return item
    return None


class TestExtractInterfaces(unittest.TestCase):
    def test_counter_widths(self):
        r = extract_interfaces.extract_interfaces(
            os.path.join(FIX, "normal", "counter.v"))
        mod = r[0]
        self.assertEqual(mod["module"], "counter")
        params = {p["name"]: p["default"] for p in mod["parameters"]}
        self.assertEqual(params["WIDTH"], "8")
        ports = {p["name"]: p for p in mod["ports"]}
        # implicit 1-bit ports keep width=None
        self.assertIsNone(ports["clk"]["width"])
        self.assertIsNone(ports["rst_n"]["width"])
        self.assertEqual(ports["count"]["width"], "WIDTH-1:0")
        self.assertEqual(ports["count"]["direction"], "output")

    def test_param_paren_default_not_truncated(self):
        r = extract_interfaces.extract_interfaces(
            os.path.join(FIX, "normal", "param_vectored.sv"))
        mod = r[0]
        params = {p["name"]: p["default"] for p in mod["parameters"]}
        # The paren default must survive intact (previously truncated at ')').
        self.assertEqual(params["DEPTH"], "$clog2(WIDTH)")
        self.assertEqual(params["WIDTH"], "8")
        ports = {p["name"]: p for p in mod["ports"]}
        self.assertEqual(ports["data_in"]["width"], "WIDTH-1:0")
        self.assertEqual(ports["data_out"]["width"], "WIDTH-1:0")
        self.assertIsNone(ports["clk"]["width"])


class TestBuildHierarchy(unittest.TestCase):
    def test_cross_file_resolution(self):
        top = os.path.join(FIX, "hierarchy", "top.sv")
        child = os.path.join(FIX, "hierarchy", "child.sv")
        r = build_hierarchy.build_hierarchy([top, child])
        top_mod = _first(r, module="top")
        self.assertIsNotNone(top_mod)
        child_inst = _first(top_mod["children"], module="child", instance="u_child")
        self.assertIsNotNone(child_inst)
        # Child must resolve to its defining file, not "未解析".
        self.assertEqual(child_inst["file"], child)

    def test_no_false_positive_on_keywords(self):
        top = os.path.join(FIX, "hierarchy", "top.sv")
        child = os.path.join(FIX, "hierarchy", "child.sv")
        r = build_hierarchy.build_hierarchy([top, child])
        top_mod = _first(r, module="top")
        child_names = {c["module"] for c in top_mod["children"]}
        # Only real module instances; 'if'/'for'/'assign' must not appear.
        self.assertEqual(child_names, {"child"})


class TestScanClockReset(unittest.TestCase):
    def test_always_ff_low_active_async_and_generated_clock(self):
        r = scan_clock_reset.scan_clock_reset(
            os.path.join(FIX, "normal", "param_vectored.sv"))
        mod = r[0]
        clk = _first(mod["clocks"], signal="clk")
        self.assertEqual(clk["edge"], "pos")
        self.assertEqual(clk["type"], "sensitivity")
        # generated clock from clk
        gclk = _first(mod["clocks"], signal="clk_div")
        self.assertEqual(gclk["type"], "generated")

        rst_n = _first(mod["resets"], signal="rst_n")
        self.assertTrue(rst_n["active_low"])
        self.assertFalse(rst_n["sync"])          # async
        self.assertIn("!rst_n", rst_n["assertion"])

        rst = _first(mod["resets"], signal="rst")
        self.assertFalse(rst["active_low"])       # active high
        self.assertTrue(rst["sync"])              # sync (only in if)
        self.assertEqual(rst["assertion"], "rst")

    def test_counter_baseline(self):
        r = scan_clock_reset.scan_clock_reset(
            os.path.join(FIX, "normal", "counter.v"))
        mod = r[0]
        clk = _first(mod["clocks"], signal="clk")
        self.assertEqual(clk["edge"], "pos")
        rst_n = _first(mod["resets"], signal="rst_n")
        self.assertTrue(rst_n["active_low"])
        self.assertFalse(rst_n["sync"])


class TestErrorIncomplete(unittest.TestCase):
    """Robustness against malformed / incomplete inputs (P2 eval guard).

    The lightweight regex tools do NOT compile RTL, so they cannot truly
    detect syntax errors. The contract verified here is:
      - tools never crash (no traceback, bounded exit code)
      - output stays parseable JSON (no fake-success prose)
      - extract_modules returns empty when the module header cannot close
        (the signal the Skill uses to flag "incomplete input")
      - multi-module files never get a fabricated top module
    """

    def _run(self, tool, path):
        proc = subprocess.run(
            [sys.executable, os.path.join(RTL, f"{tool}.py"), "--json", path],
            capture_output=True, text=True, timeout=30,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def _assert_bounded(self, rc, out, err):
        # exit code is bounded; tools are best-effort and never crash
        self.assertIn(rc, (0, 1, 2))
        self.assertNotIn("Traceback", out + err)
        # output must be parseable JSON, never fake-success prose
        data = json.loads(out)
        return data

    def test_error_file_bounded_and_no_fake_success(self):
        path = os.path.join(FIX, "error", "syntax_bad.v")
        # extract_modules cannot close the header -> empty list (incomplete signal)
        rc, out, err = self._run("extract_modules", path)
        data = self._assert_bounded(rc, out, err)
        self.assertEqual(data, [])
        # none of the four tools may claim success on a malformed file
        for tool in ("extract_interfaces", "build_hierarchy", "scan_clock_reset"):
            _rc, _out, _err = self._run(tool, path)
            self.assertNotIn("Traceback", _out + _err)
            self.assertNotIn('"success"', _out.lower())

    def test_truncated_file_bounded_and_empty_modules(self):
        path = os.path.join(FIX, "incomplete", "truncated.v")
        rc, out, err = self._run("extract_modules", path)
        data = self._assert_bounded(rc, out, err)
        self.assertEqual(data, [])  # truncated module header -> no complete module

    def test_multi_module_no_fabricated_top(self):
        path = os.path.join(FIX, "incomplete", "multi_no_top.v")
        rc, out, err = self._run("extract_modules", path)
        data = self._assert_bounded(rc, out, err)
        names = {m["name"] for m in data}
        self.assertEqual(names, {"fifo_ctrl", "arbiter", "crc8"})
        self.assertNotIn("top", names)  # no fabricated root

        _rc, _out, _err = self._run("build_hierarchy", path)
        h = self._assert_bounded(_rc, _out, _err)
        self.assertEqual({m["module"] for m in h}, names)
        for m in h:
            self.assertEqual(m["children"], [])  # no invented cross-module instances


class TestErrorIncomplete(unittest.TestCase):
    """Behavior on error / incomplete fixtures (P2): tools must not crash,
    must not fake success, and must not invent a top module."""

    def _run_cli(self, tool, rel_path):
        path = os.path.join(FIX, rel_path)
        proc = subprocess.run(
            [sys.executable, os.path.join(RTL, f"{tool}.py"), "--json", path],
            capture_output=True, text=True, timeout=30)
        return proc.returncode, proc.stdout, proc.stderr

    def _assert_bounded(self, rc, out, err):
        # best-effort parse: exit code bounded, no leaked traceback
        self.assertIn(rc, (0, 1, 2))
        self.assertNotIn("Traceback", out + err)
        data = json.loads(out)  # valid JSON, not fake-success prose
        return data

    def test_error_modules_empty_no_fake_success(self):
        # Module header cannot be closed -> extract_modules returns empty.
        rc, out, err = self._run_cli("extract_modules", "error/syntax_bad.v")
        data = self._assert_bounded(rc, out, err)
        self.assertEqual(data, [])
        # No tool may claim success on a known-bad file.
        for tool in ("extract_modules", "extract_interfaces",
                     "build_hierarchy", "scan_clock_reset"):
            _rc, _out, _err = self._run_cli(tool, "error/syntax_bad.v")
            self.assertNotIn("Traceback", _out + _err)
            self.assertNotIn('"success"', _out.lower())

    def test_truncated_modules_empty(self):
        rc, out, err = self._run_cli("extract_modules", "incomplete/truncated.v")
        data = self._assert_bounded(rc, out, err)
        self.assertEqual(data, [])  # truncated input -> no complete module header

    def test_multi_no_top_no_fabricated_top(self):
        rc, out, err = self._run_cli("extract_modules", "incomplete/multi_no_top.v")
        data = self._assert_bounded(rc, out, err)
        names = {m["name"] for m in data}
        self.assertEqual(names, {"fifo_ctrl", "arbiter", "crc8"})
        self.assertNotIn("top", names)  # do not invent a root
        # build_hierarchy must likewise not fabricate a top.
        _rc, _out, _err = self._run_cli("build_hierarchy", "incomplete/multi_no_top.v")
        h = self._assert_bounded(_rc, _out, _err)
        self.assertEqual({m["module"] for m in h}, names)
        for m in h:
            self.assertEqual(m["children"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
