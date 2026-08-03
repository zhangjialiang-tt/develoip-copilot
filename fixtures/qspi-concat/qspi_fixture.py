from __future__ import annotations

import argparse
import json
from pathlib import Path

INPUT = [0x12, 0x34, 0x56, 0x78]
EXPECTED = 0x12345678


def rtl_model(data: list[int], baseline: str) -> int:
    if baseline == "A":
        return (data[1] << 24) | (data[0] << 16) | (data[3] << 8) | data[2]
    if baseline == "B":
        return (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
    raise ValueError(f"unknown baseline: {baseline}")


def independent_reference(data: list[int]) -> int:
    return int.from_bytes(bytes(data), byteorder="big")


def run(baseline: str, data: list[int] | None = None) -> dict:
    vector = data or INPUT
    actual = rtl_model(vector, baseline)
    reference = independent_reference(vector)
    return {
        "baseline": baseline,
        "input": vector,
        "expected": EXPECTED,
        "actual": actual,
        "reference": reference,
        "passed": actual == EXPECTED,
        "independent_check_passed": actual == reference,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", choices=("A", "B"), required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.baseline), sort_keys=True))


if __name__ == "__main__":
    main()
