#!/usr/bin/env python3
"""Run simulation with a given command and capture results."""
import argparse
import subprocess
import sys
import json
from pathlib import Path


def run_simulation(command: list[str], cwd: str | None = None, timeout: int = 300) -> dict:
    """Run a simulation command and capture output."""
    result = {
        "command": " ".join(command),
        "cwd": cwd,
        "returncode": -1,
        "stdout": "",
        "stderr": "",
        "success": False,
    }

    try:
        proc = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result["returncode"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["success"] = proc.returncode == 0
    except FileNotFoundError:
        result["stderr"] = f"Error: command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        result["stderr"] = f"Error: simulation timed out after {timeout}s"
    except Exception as e:
        result["stderr"] = f"Error: {e}"

    return result


def main():
    parser = argparse.ArgumentParser(description="Run simulation and capture results")
    parser.add_argument("command", nargs="+", help="Simulation command to execute")
    parser.add_argument("--cwd", help="Working directory for simulation")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    result = run_simulation(args.command, args.cwd, args.timeout)

    if args.json:
        # Truncate output for JSON
        result["stdout"] = result["stdout"][:10000]
        result["stderr"] = result["stderr"][:10000]
        print(json.dumps(result, indent=2))
    else:
        print(f"Command: {result['command']}")
        print(f"Return code: {result['returncode']}")
        print(f"Success: {result['success']}")
        if result["stdout"]:
            print(f"\n--- stdout ---\n{result['stdout'][:5000]}")
        if result["stderr"]:
            print(f"\n--- stderr ---\n{result['stderr'][:5000]}")


if __name__ == "__main__":
    main()
