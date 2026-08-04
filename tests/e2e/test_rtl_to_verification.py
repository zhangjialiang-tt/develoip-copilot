#!/usr/bin/env python3
"""End-to-end test for RTL analysis and simulation log parsing.

This test validates the complete flow:
RTL input → RTL structure extraction → structured analysis result →
simulation log parsing → PASS/FAIL determination
"""
import pytest
import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return the result."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check
    )
    return result


class TestRTLAnalysisE2E:
    """Test end-to-end RTL analysis flow."""

    def test_rtl_extraction_counter_normal(self):
        """Test RTL extraction on normal counter.v."""
        result = run_command([
            "python", "tools/rtl/integrate_analysis.py",
            "fixtures/rtl/normal/counter.v",
            "--json"
        ])

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        analysis = json.loads(result.stdout)

        # Validate basic structure
        assert analysis["schema_version"] == "1.0"
        assert analysis["top_module"] == "counter"
        assert analysis["status"] == "COMPLETE"

        # Validate parameters
        assert len(analysis["parameters"]) == 1
        assert analysis["parameters"][0]["name"] == "WIDTH"
        assert analysis["parameters"][0]["default"] == "8"

        # Validate ports
        assert len(analysis["ports"]) == 4
        port_names = [p["name"] for p in analysis["ports"]]
        assert "clk" in port_names
        assert "rst_n" in port_names
        assert "enable" in port_names
        assert "count" in port_names

        # Validate clocks
        assert len(analysis["clocks"]) == 1
        assert analysis["clocks"][0]["name"] == "clk"
        assert analysis["clocks"][0]["edge"] == "posedge"
        assert analysis["clocks"][0]["confidence"] == "HIGH"

        # Validate resets
        assert len(analysis["resets"]) == 1
        assert analysis["resets"][0]["name"] == "rst_n"
        assert analysis["resets"][0]["active_level"] == "LOW"
        assert analysis["resets"][0]["kind"] == "ASYNC"
        assert analysis["resets"][0]["confidence"] == "HIGH"

    def test_rtl_extraction_counter_buggy(self):
        """Test RTL extraction on buggy counter.v."""
        result = run_command([
            "python", "tools/rtl/integrate_analysis.py",
            "fixtures/rtl/normal/counter_buggy.v",
            "--json"
        ])

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        analysis = json.loads(result.stdout)

        # Buggy counter should have same structure as normal
        assert analysis["top_module"] == "counter_buggy"
        assert len(analysis["ports"]) == 4
        assert len(analysis["clocks"]) == 1
        assert len(analysis["resets"]) == 1

    def test_rtl_extraction_nonexistent_file(self):
        """Test that nonexistent file returns non-zero exit code."""
        result = run_command([
            "python", "tools/rtl/integrate_analysis.py",
            "nonexistent.v",
            "--json"
        ], check=False)

        assert result.returncode != 0
        assert "file not found" in result.stderr

    def test_rtl_schema_compliance(self):
        """Test that analysis output complies with schema."""
        result = run_command([
            "python", "tools/rtl/integrate_analysis.py",
            "fixtures/rtl/normal/counter.v",
            "--json"
        ])

        assert result.returncode == 0

        analysis = json.loads(result.stdout)

        # Check required fields
        required_fields = [
            "schema_version", "top_module", "source_files",
            "parameters", "ports", "clocks", "resets",
            "instances", "unsupported_constructs", "uncertainties", "status"
        ]

        for field in required_fields:
            assert field in analysis, f"Missing required field: {field}"

    def test_behavior_spec_exists(self):
        """Test that behavior specification file exists."""
        spec_file = Path("fixtures/rtl/normal/counter.spec.yaml")
        assert spec_file.exists()

        # Basic content validation
        content = spec_file.read_text()
        assert "top_module: counter" in content
        assert "clock:" in content
        assert "reset:" in content
        assert "expected behavior" in content.lower()


class TestSimulationLogParsingE2E:
    """Test end-to-end simulation log parsing."""

    def test_log_parsing_pass_case(self):
        """Test log parsing on PASS case."""
        result = run_command([
            "python", "tools/simulation/parse_log.py",
            "fixtures/simulation/normal/sim_pass.log",
            "--json"
        ])

        assert result.returncode == 0

        results = json.loads(result.stdout)
        assert len(results) == 1

        log_result = results[0]
        assert log_result["status"] == "PASS"
        assert log_result["summary"]["test_result"] == "PASSED"
        assert log_result["summary"]["error_count"] == 0
        assert len(log_result["errors"]) == 0

    def test_log_parsing_fail_case(self):
        """Test log parsing on FAIL case."""
        result = run_command([
            "python", "tools/simulation/parse_log.py",
            "fixtures/simulation/error/sim_fail.log",
            "--json"
        ])

        assert result.returncode == 0

        results = json.loads(result.stdout)
        assert len(results) == 1

        log_result = results[0]
        assert log_result["status"] == "FAIL"
        assert log_result["summary"]["test_result"] == "FAILED"
        assert log_result["summary"]["error_count"] == 2
        assert len(log_result["errors"]) > 0
        assert len(log_result["assertions"]) > 0

    def test_log_parsing_inconsistent_case(self):
        """Test log parsing on evidence conflict case."""
        result = run_command([
            "python", "tools/simulation/parse_log.py",
            "fixtures/simulation/error/sim_conflict.log",
            "--json"
        ])

        assert result.returncode == 0

        results = json.loads(result.stdout)
        assert len(results) == 1

        log_result = results[0]
        assert log_result["status"] == "INCONSISTENT"
        # Should have both assertion failures and PASSED marker
        assert len(log_result["assertions"]) > 0
        assert log_result["summary"]["test_result"] == "PASSED"
        assert log_result["summary"]["error_count"] == 0

    def test_log_parsing_nonexistent_file(self):
        """Test that nonexistent log file returns non-zero exit code."""
        result = run_command([
            "python", "tools/simulation/parse_log.py",
            "nonexistent.log",
            "--json"
        ], check=False)

        assert result.returncode != 0
        assert "file not found" in result.stderr

    def test_failure_extraction_first_only(self):
        """Test that extract_failures.py returns first failure."""
        result = run_command([
            "python", "tools/simulation/extract_failures.py",
            "fixtures/simulation/error/sim_fail.log",
            "--first-only",
            "--json"
        ])

        assert result.returncode == 0

        failures = json.loads(result.stdout)
        assert len(failures) == 1
        assert failures[0]["type"] in ["assertion", "error"]
        assert "message" in failures[0]

    def test_normal_dut_pass_simulation(self):
        """Test that normal DUT would produce PASS simulation result.

        This is a logical test based on the RTL structure and behavior spec.
        """
        # Load RTL analysis
        rtl_result = run_command([
            "python", "tools/rtl/integrate_analysis.py",
            "fixtures/rtl/normal/counter.v",
            "--json"
        ])
        assert rtl_result.returncode == 0
        analysis = json.loads(rtl_result.stdout)

        # Validate counter structure matches expected behavior
        assert analysis["top_module"] == "counter"
        assert any(p["name"] == "count" for p in analysis["ports"])

        # Load behavior spec
        spec_file = Path("fixtures/rtl/normal/counter.spec.yaml")
        assert spec_file.exists()
        spec_content = spec_file.read_text()

        # Check that spec defines expected behavior
        assert "increment" in spec_content.lower()
        assert "reset" in spec_content.lower()

        # If testbench were generated and simulation run,
        # normal counter should produce PASS result
        # (This is a logical assertion, not actual simulation)

    def test_error_dut_fail_simulation(self):
        """Test that error DUT would produce FAIL simulation result.

        This is a logical test based on the RTL structure and behavior spec.
        """
        # Load buggy RTL analysis
        rtl_result = run_command([
            "python", "tools/rtl/integrate_analysis.py",
            "fixtures/rtl/normal/counter_buggy.v",
            "--json"
        ])
        assert rtl_result.returncode == 0
        analysis = json.loads(rtl_result.stdout)

        # Buggy counter has same structure but different behavior
        assert analysis["top_module"] == "counter_buggy"

        # Read the buggy RTL to confirm the error
        buggy_rtl = Path("fixtures/rtl/normal/counter_buggy.v").read_text()
        assert "+ 2" in buggy_rtl  # The bug: increments by 2 instead of 1

        # If testbench were generated with reference model (increment by 1),
        # buggy counter would produce FAIL result
        # (This is a logical assertion, not actual simulation)


class TestFailurePathsE2E:
    """Test failure paths in the end-to-end flow."""

    def test_missing_top_module(self):
        """Test behavior when top module is ambiguous."""
        # Use a file with multiple modules
        result = run_command([
            "python", "tools/rtl/integrate_analysis.py",
            "fixtures/rtl/incomplete/multi_no_top.v",
            "--json"
        ], check=False)

        assert result.returncode != 0
        assert "top_module" in result.stderr.lower() or "modules" in result.stderr.lower()

    def test_invalid_log_format(self):
        """Test behavior with invalid log format."""
        # Create a temporary invalid log file
        invalid_log = Path("fixtures/simulation/error/invalid.log")
        invalid_log.write_text("This is not a valid simulation log")

        result = run_command([
            "python", "tools/simulation/parse_log.py",
            str(invalid_log),
            "--json"
        ], check=False)

        # Should not crash, but return UNKNOWN status
        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert results[0]["status"] == "UNKNOWN"

        # Clean up
        invalid_log.unlink()

    def test_empty_log_file(self):
        """Test behavior with empty log file."""
        # Create a temporary empty log file
        empty_log = Path("fixtures/simulation/error/empty.log")
        empty_log.write_text("")

        result = run_command([
            "python", "tools/simulation/parse_log.py",
            str(empty_log),
            "--json"
        ])

        assert result.returncode == 0
        results = json.loads(result.stdout)
        assert results[0]["status"] == "UNKNOWN"

        # Clean up
        empty_log.unlink()


class TestToolExitCodesE2E:
    """Test that tools return appropriate exit codes."""

    def test_rtl_tools_exit_on_error(self):
        """Test that RTL tools return non-zero exit code on errors."""
        tools_to_test = [
            ("tools/rtl/extract_modules.py", ["nonexistent.v"]),
            ("tools/rtl/extract_interfaces.py", ["nonexistent.v"]),
            ("tools/rtl/scan_clock_reset.py", ["nonexistent.v"]),
        ]

        for tool, args in tools_to_test:
            result = run_command(["python", tool] + args, check=False)
            assert result.returncode != 0, f"{tool} should return non-zero for missing file"

    def test_simulation_tools_exit_on_error(self):
        """Test that simulation tools return non-zero exit code on errors."""
        tools_to_test = [
            ("tools/simulation/parse_log.py", ["nonexistent.log"]),
            ("tools/simulation/extract_failures.py", ["nonexistent.log"]),
        ]

        for tool, args in tools_to_test:
            result = run_command(["python", tool] + args, check=False)
            assert result.returncode != 0, f"{tool} should return non-zero for missing file"

    def test_sim_run_nonexistent_command(self):
        """Test that run.py handles nonexistent command gracefully."""
        result = run_command([
            "python", "tools/simulation/run.py",
            "nonexistent_command_xyz",
            "--json"
        ], check=False)

        # Should not crash
        assert result.returncode == 0
        result_json = json.loads(result.stdout)
        assert result_json["success"] == False
        assert "command not found" in result_json["stderr"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])