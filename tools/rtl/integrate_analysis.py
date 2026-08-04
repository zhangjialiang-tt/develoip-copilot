#!/usr/bin/env python3
"""Integrate multiple RTL analysis tools into a structured JSON output."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess

# Get the tools directory (tools/)
TOOLS_DIR = Path(__file__).parent.parent


def run_tool(script_name, args):
    """Run a Python tool and return its JSON output."""
    script_path = TOOLS_DIR / script_name

    try:
        result = subprocess.run(
            ["python", str(script_path)] + args,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from {script_name}: {e}", file=sys.stderr)
        sys.exit(1)


def integrate_analysis(filepath: str, top_module: str = None) -> dict:
    """Integrate RTL analysis from multiple tools into a structured output."""
    path = Path(filepath)
    if not path.exists():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    # Run individual tools
    modules = run_tool(
        "rtl/extract_modules.py",
        [filepath, "--json"]
    )

    interfaces = run_tool(
        "rtl/extract_interfaces.py",
        [filepath, "--json"]
    )

    clock_reset = run_tool(
        "rtl/scan_clock_reset.py",
        [filepath, "--json"]
    )

    # Determine top module
    if top_module:
        top = top_module
    elif len(modules) == 1:
        top = modules[0]["name"]
    else:
        print(f"Error: {len(modules)} modules found, please specify top_module with --top", file=sys.stderr)
        print(f"Available modules: {[m['name'] for m in modules]}", file=sys.stderr)
        sys.exit(1)

    # Find the top module data
    top_module_data = None
    for m in modules:
        if m["name"] == top:
            top_module_data = m
            break

    if not top_module_data:
        print(f"Error: top module '{top}' not found", file=sys.stderr)
        sys.exit(1)

    # Find interface data for top module
    top_interfaces = None
    for iface in interfaces:
        if iface.get("module") == top:
            top_interfaces = iface
            break

    if not top_interfaces:
        print(f"Error: no interface data found for module '{top}'", file=sys.stderr)
        sys.exit(1)

    # Find clock/reset data for top module
    top_clock_reset = None
    for cr in clock_reset:
        if cr.get("module") == top:
            top_clock_reset = cr
            break

    if not top_clock_reset:
        print(f"Warning: no clock/reset data found for module '{top}'", file=sys.stderr)
        top_clock_reset = {"clocks": [], "resets": []}

    # Build structured output
    result = {
        "schema_version": "1.0",
        "top_module": top,
        "source_files": [str(path.absolute())],
        "parameters": [],
        "ports": [],
        "clocks": [],
        "resets": [],
        "instances": [],
        "unsupported_constructs": [],
        "uncertainties": [],
        "status": "COMPLETE",
        "analysis_timestamp": datetime.now().isoformat(),
        "tool_versions": {
            "extract_modules": "1.0",
            "extract_interfaces": "1.0",
            "scan_clock_reset": "1.0",
            "build_hierarchy": "1.0"
        }
    }

    # Extract parameters
    if "parameters" in top_interfaces:
        for param in top_interfaces["parameters"]:
            result["parameters"].append({
                "name": param["name"],
                "default": param.get("default"),
                "width": param.get("width")
            })

    # Extract ports
    if "ports" in top_interfaces:
        for port in top_interfaces["ports"]:
            result["ports"].append({
                "name": port["name"],
                "direction": port["direction"],
                "width_expression": port.get("width"),
                "source_file": top_module_data["file"],
                "source_line": top_module_data["line"]
            })

    # Extract clocks
    if "clocks" in top_clock_reset:
        for clk in top_clock_reset["clocks"]:
            edge = "UNKNOWN"
            if clk.get("edge") == "pos":
                edge = "posedge"
            elif clk.get("edge") == "neg":
                edge = "negedge"

            result["clocks"].append({
                "name": clk["signal"],
                "edge": edge,
                "confidence": "HIGH" if clk.get("type") == "sensitivity" else "MEDIUM"
            })

    # Extract resets
    if "resets" in top_clock_reset:
        for rst in top_clock_reset["resets"]:
            active_level = "UNKNOWN"
            if rst.get("active_low"):
                active_level = "LOW"
            else:
                active_level = "HIGH"

            kind = "UNKNOWN"
            if not rst.get("sync", True):  # async if sync is False
                kind = "ASYNC"
            else:
                kind = "SYNC"

            result["resets"].append({
                "name": rst["signal"],
                "active_level": active_level,
                "kind": kind,
                "confidence": "HIGH" if rst.get("assertion") else "MEDIUM"
            })

    # Determine status based on uncertainties
    uncertainties = []
    if not result["clocks"]:
        uncertainties.append({
            "field": "clocks",
            "reason": "No clock signals detected"
        })
        result["status"] = "PARTIAL"

    if not result["resets"]:
        uncertainties.append({
            "field": "resets",
            "reason": "No reset signals detected"
        })
        result["status"] = "PARTIAL"

    result["uncertainties"] = uncertainties

    return result


def main():
    parser = argparse.ArgumentParser(description="Integrate RTL analysis from multiple tools")
    parser.add_argument("filepath", help="RTL file to analyze")
    parser.add_argument("--top", help="Top module name (required if multiple modules exist)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    args = parser.parse_args()

    result = integrate_analysis(args.filepath, args.top)

    if args.json or args.output:
        output = json.dumps(result, indent=2)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Analysis result written to {args.output}", file=sys.stderr)
        else:
            print(output)
    else:
        print(f"Top Module: {result['top_module']}")
        print(f"Status: {result['status']}")
        print(f"Parameters: {len(result['parameters'])}")
        print(f"Ports: {len(result['ports'])}")
        print(f"Clocks: {len(result['clocks'])}")
        print(f"Resets: {len(result['resets'])}")
        if result["uncertainties"]:
            print(f"Uncertainties: {len(result['uncertainties'])}")
            for u in result["uncertainties"]:
                print(f"  - {u['field']}: {u['reason']}")


if __name__ == "__main__":
    main()