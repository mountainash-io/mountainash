"""End-to-end tests: real Frictionless descriptor → DataPackage → RelationDAG → DataPackage."""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from mountainash.typespec.datapackage import DataPackage

FIXTURES = Path(__file__).parent.parent.parent / "typespec" / "fixtures"


def _to_eager(result: object) -> pl.DataFrame:
    if isinstance(result, pl.LazyFrame):
        return result.collect()
    if isinstance(result, pl.DataFrame):
        return result
    raise TypeError(f"Expected pl.LazyFrame or pl.DataFrame, got {type(result)}")


def _stub_resources(raw: dict, tmp_path: Path, *, drop_schema: bool = True) -> dict:
    """Rewrite every tabular resource's path to a local CSV stub.

    Parameters
    ----------
    drop_schema:
        When True (default), strip ``schema`` from each resource so conform
        is not attempted on the stub data.  Set False only when the stub data
        is type-compatible with the full schema.
    """
    for r in raw["resources"]:
        local = tmp_path / f"{r['name']}.csv"
        schema = r.get("schema") or {}
        fields = schema.get("fields") or []
        if fields:
            header = ",".join(f["name"] for f in fields)
            row = ",".join(
                "0" if f.get("type") in {"integer", "number", "year"} else "x"
                for f in fields
            )
            local.write_text(f"{header}\n{row}\n")
        else:
            local.write_text("col\nx\n")
        r["path"] = str(local)
        if drop_schema:
            r.pop("schema", None)
    return raw


def test_descriptor_round_trip_through_dag(tmp_path: Path) -> None:
    """Real descriptor → DataPackage → RelationDAG → back to DataPackage."""
    raw = json.loads((FIXTURES / "gdp.datapackage.json").read_text())

    # Capture the original schemas before stubbing drops them
    original_schemas = {
        r["name"]: r.get("schema") for r in raw["resources"] if r.get("schema")
    }

    raw = _stub_resources(raw, tmp_path, drop_schema=True)

    pkg = DataPackage.from_descriptor(raw)
    dag = pkg.to_relation_dag()
    pkg2 = dag.to_package()

    # Round-trip preserves resource names
    assert {r.name for r in pkg2.resources} == {r.name for r in pkg.resources}

    # After dropping schemas from stub, pkg.resources have no table_schema —
    # the round-trip should also produce no table_schema (symmetric)
    schemas_out = {r.name: r.table_schema for r in pkg2.resources if r.table_schema}
    assert schemas_out == {}


def test_descriptor_round_trip_preserves_schema(tmp_path: Path) -> None:
    """When schemas are present, round-trip preserves them byte-for-byte."""
    raw = json.loads((FIXTURES / "gdp.datapackage.json").read_text())

    # Capture original schemas before stubbing paths (without dropping schema)
    schemas_before = {
        r["name"]: r.get("schema") for r in raw["resources"] if r.get("schema")
    }

    # Only stub the paths; keep the schemas intact
    for r in raw["resources"]:
        local = tmp_path / f"{r['name']}.csv"
        schema = r.get("schema") or {}
        fields = schema.get("fields") or []
        if fields:
            header = ",".join(f["name"] for f in fields)
            row = ",".join(
                "0" if f.get("type") in {"integer", "number", "year"} else "x"
                for f in fields
            )
            local.write_text(f"{header}\n{row}\n")
        else:
            local.write_text("col\nx\n")
        r["path"] = str(local)

    pkg = DataPackage.from_descriptor(raw)
    dag = pkg.to_relation_dag()
    pkg2 = dag.to_package()

    # Resource names round-trip
    assert {r.name for r in pkg2.resources} == {r.name for r in pkg.resources}

    # Table schemas round-trip (dict equality is order-independent)
    schemas_after = {r.name: r.table_schema for r in pkg2.resources if r.table_schema}
    assert schemas_before == schemas_after


def test_descriptor_collect_one_resource(tmp_path: Path) -> None:
    """End-to-end: descriptor → DAG → collect a single resource into a DataFrame."""
    raw = json.loads((FIXTURES / "gdp.datapackage.json").read_text())

    target_name = raw["resources"][0]["name"]
    raw = _stub_resources(raw, tmp_path, drop_schema=True)

    pkg = DataPackage.from_descriptor(raw)
    dag = pkg.to_relation_dag()
    result = dag.collect(target_name)
    df = _to_eager(result)
    assert df.shape[0] >= 1


def test_descriptor_collect_all_resources(tmp_path: Path) -> None:
    """Collect every tabular resource from the GDP descriptor without error."""
    raw = json.loads((FIXTURES / "gdp.datapackage.json").read_text())
    raw = _stub_resources(raw, tmp_path, drop_schema=True)

    pkg = DataPackage.from_descriptor(raw)
    dag = pkg.to_relation_dag()

    for name in dag.relations:
        result = dag.collect(name)
        df = _to_eager(result)
        assert df.shape[0] >= 1, f"Expected at least one row for resource {name!r}"
