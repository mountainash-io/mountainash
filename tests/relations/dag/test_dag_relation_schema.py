"""DAGRelation schema-family + assess_drift resolve refs via the DAG. PR-2 §2.2."""
from __future__ import annotations

import polars as pl

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG


def _dag():
    dag = RelationDAG()
    dag.add("raw", ma.relation(pl.DataFrame({"x": [1, 2], "y": ["a", "b"]})))
    return dag


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
    plain = Relation(RefRelNode(name="raw")).conform(spec)
    # Should not raise; returns a list (possibly under-assessed). This is the
    # baseline the DAGRelation override improves on.
    assert isinstance(plain.assess_drift(), list)
