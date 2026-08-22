"""Pre-computes Contract B for each synthetic fixture and writes it to disk,
so Workstream 03/04 can build and demo against real pricing output without
running Python or waiting on a live request.

Run with: python -m pricing.generate_fixtures
"""

import copy
import json
import os

from .engine import analyze
from .fixtures import ALL_FIXTURES

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "demo_cache")


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name, contract_a in ALL_FIXTURES.items():
        result = analyze(copy.deepcopy(contract_a))
        payload = {"contract_a": contract_a, "contract_b": result}
        path = os.path.join(OUTPUT_DIR, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"wrote {path}  (risk_score={result['risk_score']['overall']}, premium=${result['annual_premium']})")


if __name__ == "__main__":
    main()
