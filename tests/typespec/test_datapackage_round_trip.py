"""Round-trip tests against real datapackage.json fixtures fetched from github.com/datasets/."""
import json
from pathlib import Path

import pytest

from mountainash import DescriptorWriteMode
from mountainash.typespec.datapackage import DataPackage

FIXTURES = Path(__file__).parent / "fixtures"


def test_write_defaults_to_preserve(tmp_path):
    raw = {
        "$schema": "https://datapackage.org/profiles/2.0/datapackage.json",
        "contributors": [{"title": "Author", "role": "author"}],
        "resources": [{"name": "orders", "path": "orders.csv"}],
    }
    path = tmp_path / "datapackage.json"
    DataPackage.from_descriptor(raw).write(path)
    assert json.loads(path.read_text()) == raw


def test_preserve_serialization_reads_public_package_sources() -> None:
    package = DataPackage(
        sources=[{"title": "catalog", "meta": {"tags": ["a"]}}],
        resources=[{"name": "orders", "path": "orders.csv"}],
    )
    package.sources[0]["meta"]["tags"].append("model-change")

    assert package.to_descriptor()["sources"] == [
        {"title": "catalog", "meta": {"tags": ["a", "model-change"]}}
    ]


def test_write_accepts_explicit_canonical_mode(tmp_path):
    raw = {
        "contributors": [{"title": "Author", "role": "author"}],
        "resources": [{"name": "orders", "path": "orders.csv"}],
    }
    path = tmp_path / "datapackage.json"
    DataPackage.from_descriptor(raw).write(path, mode=DescriptorWriteMode.CANONICAL)
    result = json.loads(path.read_text())
    assert result["$schema"] == "https://datapackage.org/profiles/2.0/datapackage.json"
    assert result["contributors"] == [{"title": "Author", "roles": ["author"]}]

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
