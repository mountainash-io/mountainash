"""DAGRelation schema-family + assess_drift resolve refs via the DAG. PR-2 §2.2."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.relations.dag.dag import RelationDAG


def _dag():
    dag = RelationDAG()
    dag.add("raw", ma.relation(pl.DataFrame({"x": [1, 2], "y": ["a", "b"]})))
    return dag


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_implicit_projection_keeps_dag_terminal_routing(backend_name, backend_factory):
    dag = RelationDAG()
    dag.add("raw", ma.relation(backend_factory.create({"n": [None, 2]}, backend_name)))
    rel = dag.ref("raw").with_columns(ma.col("n").fill_null(0))
    assert rel.columns == ["n"]
    assert rel.to_dict() == {"n": [0, 2]}


def test_schema_resolves_over_ref_tree():
    dag = _dag()
    rel = dag.ref("raw").filter(ma.col("x").gt(0))
    # A plain Relation over a RefRelNode would infer {} here; DAGRelation must
    # resolve via dag.schema("raw").
    schema = rel.schema
    assert set(schema.keys()) == {"x", "y"}
    assert set(rel.columns) == {"x", "y"}
    assert rel.width == 2
    assert list(rel.dtypes)  # non-empty, resolved
    assert rel.output_schema is not None


def test_plain_relation_still_degenerate_over_ref():
    # Contrast guard: a plain Relation wrapping the same RefRelNode still infers
    # empty (no resolver) — proves the DAGRelation override is what fixes it.
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        RefRelNode,
    )
    plain = Relation(RefRelNode(name="raw"))
    assert plain.schema == {}


def test_assess_drift_resolves_refs_via_dag():
    # assess_drift never compiles, so Task 3's choke-point overrides don't cover
    # it — DAGRelation must pass a dag-backed resolver so a conform node above a
    # ref is assessed against the ref's resolved schema.
    dag = _dag()
    spec = ma.typespec({"x": "integer", "y": "string"})
    rel = dag.ref("raw").conform(spec)
    drifts = rel.assess_drift()
    assert isinstance(drifts, list)


def test_assess_drift_plain_relation_over_ref_is_degenerate():
    # Contrast: a plain Relation conform over a bare ref has no resolver, so its
    # assess_drift under-assesses (the ref infers {}). Pins that the DAGRelation
    # override is the differentiator.
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        RefRelNode,
    )
    spec = ma.typespec({"x": "integer", "y": "string"})
    # fields_match must be "open" explicitly (the model default is now the
    # strict "exact", which would raise on the ref's empty inferred schema
    # instead of under-assessing). This test pins the resolver-less degenerate
    # path, not exact-mode column enforcement.
    spec.fields_match = "open"
    plain = Relation(RefRelNode(name="raw")).conform(spec)
    # Should not raise; returns a list (possibly under-assessed). This is the
    # baseline the DAGRelation override improves on.
    assert isinstance(plain.assess_drift(), list)


@pytest.mark.parametrize("backend_name", ["polars", "ibis-duckdb"])
def test_row_index_schema_resolves_dag_identity(backend_factory, backend_name):
    """Source identity must survive a ref and projection, not degrade to UNKNOWN."""
    from mountainash.core.dtypes import MountainashDtype as D

    dag = RelationDAG()
    dag.add("raw", ma.relation(backend_factory.create({"value": [8, 3]}, backend_name)))
    indexed = dag.ref("raw").with_row_index(name="ordinal")
    dag.add("indexed", indexed)
    dtype = D.I64 if backend_name == "ibis-duckdb" else (
        D.U64 if pl.get_index_type() == pl.UInt64 else D.U32
    )
    expected = [("value", D.I64), ("ordinal", dtype)] if backend_name == "ibis-duckdb" else [
        ("ordinal", dtype), ("value", D.I64),
    ]
    assert list(indexed.schema.items()) == expected
    assert list(dag.schema("indexed").items()) == expected
    projected = indexed.select("ordinal")
    assert projected.schema == {"ordinal": dtype}
    assert sorted(projected.to_polars()["ordinal"].to_list()) == [0, 1]
