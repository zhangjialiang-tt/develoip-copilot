import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from qspi_fixture import run  # noqa: E402


if __name__ == "__main__":
    baseline = sys.argv[1] if len(sys.argv) > 1 else "A"
    print(json.dumps(run(baseline), sort_keys=True))
