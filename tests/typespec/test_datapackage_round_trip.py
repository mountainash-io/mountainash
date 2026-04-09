"""Round-trip tests against real datapackage.json fixtures fetched from github.com/datasets/."""
import json
from pathlib import Path

import pytest

from mountainash.typespec.datapackage import DataPackage

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("name", ["gdp", "gold-prices"])
def test_real_descriptor_round_trips(name):
    raw = json.loads((FIXTURES / f"{name}.datapackage.json").read_text())
    pkg = DataPackage.from_descriptor(raw)
    result = pkg.to_descriptor()
    if result != raw:
        import pprint
        print("\n--- RAW ---")
        pprint.pprint(raw)
        print("\n--- RESULT ---")
        pprint.pprint(result)
        # Print diff of keys
        raw_keys = set(raw.keys())
        result_keys = set(result.keys())
        print(f"\nKeys only in raw: {raw_keys - result_keys}")
        print(f"Keys only in result: {result_keys - raw_keys}")
    assert result == raw
