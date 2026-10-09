"""Public scoped fingerprints: source selection, ownership and capability checks."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS, REGISTRY
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.errors import MaterializationScopeClosedError, LogicalTerminalRequired

SUPPORTED = {"polars", "polars-lazy", "ibis-duckdb"}


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_public_scope_and_unsupported_routes(backend_name):
    source = REGISTRY[backend_name].build({"a": [1, 1, 2], "b": [10, 11, 10], "v": [7, 8, 9]}, "fingerprint_scope")
    rel = ma.relation(source).filter(ma.col("a") == 1)
    if backend_name not in SUPPORTED:
        with pytest.raises(BackendCapabilityError, match="bounded"):
            rel.fingerprint(keys=["a", "b"], columns=["v"])
    else:
        out = rel.fingerprint(keys=["a", "b"], columns=["v"], batch_size=1)
        assert out["row_count"].to_list() == [2, 2]
        assert out["column"].to_list() == [None, "v"]


@pytest.mark.parametrize("backend_name", sorted(SUPPORTED))
@pytest.mark.parametrize("change,expected_keys,expected_values", [
    ("inside", False, True), ("outside", False, False), ("ignored", False, False),
    ("delete", True, True), ("duplicate", True, True), ("leave", True, True),
    ("enter", True, True), ("swap", False, True),
])
def test_mutations_respect_both_scopes(backend_name, change, expected_keys, expected_values):
    data = {"a": [1, 1, 2], "b": [10, 11, 10], "v": [7, 8, 9], "ignored": [0, 0, 0]}
    def calculate(values, name):
        rel = ma.relation(REGISTRY[backend_name].build(values, name))
        return rel.filter(ma.col("a") == 1).fingerprint(keys=["a", "b"], columns=["v"], batch_size=1)
    base = calculate(data, "fp_base")
    data = {k: list(v) for k, v in data.items()}
    if change == "inside":
        data["v"][0] = 12
    elif change == "outside":
        data["v"][2] = 12
    elif change == "ignored":
        data["ignored"][0] = 12
    elif change == "leave":
        data["a"][0] = 3
    elif change == "enter":
        data["a"][2] = 1
    elif change == "swap":
        data["v"][:2] = [8, 7]
    elif change == "delete":
        data = {k: v[1:] for k, v in data.items()}
    elif change == "duplicate":
        data = {k: v + v[:1] for k, v in data.items()}
    current = calculate(data, "fp_current")
    assert (base.row(0) != current.row(0)) is expected_keys
    assert (base.row(1) != current.row(1)) is expected_values


@pytest.mark.parametrize("backend_name", sorted(SUPPORTED))
def test_missing_key_and_typed_empty(backend_name):
    rel = ma.relation(REGISTRY[backend_name].build({"k": [1], "v": [7]}, "empty_scope"))
    empty = rel.filter(ma.col("k") < 0).fingerprint(keys=["k"], columns=["v"])
    assert empty["row_count"].to_list() == [0, 0]
    assert empty["value_schema"][1] == '["v",{"type":"Int64"}]'
    with pytest.raises(Exception, match="k"):
        rel.select("v").fingerprint(keys=["k"], columns=["v"])


def test_dag_terminal_preserves_resolver_and_does_not_register():
    dag = ma.RelationDAG()
    dag.add("source", ma.relation(pl.DataFrame({"k": [1, 2], "v": [3, 4]})))
    before = tuple(dag.dependency_edges)
    out = dag.ref("source").filter(ma.col("k") == 2).fingerprint(keys=["k"], columns=["v"])
    assert out["row_count"].to_list() == [1, 1]
    assert tuple(dag.dependency_edges) == before


def test_closed_snapshot_and_detached_result():
    with ma.materialization_scope() as scope:
        saved = scope.snapshot(ma.relation(pl.DataFrame({"k": [1], "v": [7]})))
        out = saved.fingerprint(keys=["k"], columns=["v"])
    assert out["row_count"].to_list() == [1, 1]
    with pytest.raises(MaterializationScopeClosedError):
        saved.fingerprint(keys=["k"], columns=["v"])


@pytest.mark.parametrize("bad", [0, -1, True, 1.5])
def test_invalid_batch_rejected_before_missing_source(bad):
    with pytest.raises((ValueError, TypeError), match="batch_size"):
        ma.relation(pl.DataFrame({"k": [1]})).fingerprint(keys=["k"], columns=["missing"], batch_size=bad)


def test_late_source_residue_never_returns_a_partial_fingerprint(checked_year):
    source = REGISTRY["ibis-duckdb"].build({"id": [1, 2], "year": ["2024", "bad"]}, "fp_residue")
    rel = ma.relation(source).conform(checked_year)
    with pytest.raises(BackendCapabilityError, match="year residue"):
        rel.fingerprint(keys=["id"], columns=["year"], batch_size=1)


def test_physical_structured_encoding_is_not_hashed_as_logical_data():
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    source = pl.DataFrame({"k": [1], "payload": ['[1,2]'], "v": [7]})
    rel = ma.relation(source).conform(TypeSpec(fields_match="open", fields=[
        FieldSpec(name="payload", type=UniversalType.ARRAY)]))
    with pytest.raises(LogicalTerminalRequired):
        rel.fingerprint(keys=["k"], columns=["payload"])
    assert rel.fingerprint(keys=["k"], columns=["v"])["row_count"].to_list() == [1, 1]
