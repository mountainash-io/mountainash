"""Tests for `Relation.collect_with_drift()` and `Relation.assess_drift()`.

Item 48 Task 9 (final task of PR-B): the ONE report terminal
(`collect_with_drift`, returning a `ConformCollection`) plus the schema-only
pre-flight (`assess_drift`, returning `list[ConformDrift]`, never raising).

Both share the underlying `_compile_and_execute_with_visitor` /
`UnifiedRelationVisitor.drift_reports` (execute path) and
`schema_inference.assess_drift` (infer path) plumbing exercised more
granularly in `test_visitor_conform.py` and `test_schema_inference_conform.py`
-- this module tests the two new `Relation` terminals themselves: the
ordering guarantee across multiple conform nodes, the freeze fail-fast
identity, and that `assess_drift` truly never raises.

Polars-only by design: the mechanism under test (visitor plumbing, AST
traversal order) is backend-agnostic and already re-verified per-backend for
the underlying data_type policies in `cross_backend/test_conform_drift.py`.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.drift import ConformCollection, ConformDrift
from mountainash.conform.errors import SchemaDriftError
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType as U


# ---------------------------------------------------------------------------
# collect_with_drift() -- single conform node
# ---------------------------------------------------------------------------

class TestCollectWithDriftBasics:
    def test_returns_conform_collection(self):
        df = pl.DataFrame({"n": [1, 2]})
        spec = TypeSpec(fields=[FieldSpec(name="n", type=U.INTEGER)])
        rel = ma.relation(df).conform(spec)

        collection = rel.collect_with_drift()

        assert isinstance(collection, ConformCollection)
        assert collection.frame["n"].to_list() == [1, 2]
        assert len(collection.drifts) == 1
        assert isinstance(collection.drift, ConformDrift)

    def test_frame_is_materialized_not_a_lazy_plan(self):
        """collect_with_drift is a terminal -- the frame must be eager,
        mirroring collect()'s own LazyFrame -> DataFrame unwrap contract."""
        lf = pl.DataFrame({"n": [1, 2]}).lazy()
        spec = TypeSpec(fields=[FieldSpec(name="n", type=U.INTEGER)])
        rel = ma.relation(lf).conform(spec)

        collection = rel.collect_with_drift()

        assert isinstance(collection.frame, pl.DataFrame)

    def test_no_conform_node_yields_empty_drifts(self):
        df = pl.DataFrame({"n": [1, 2]})
        rel = ma.relation(df).filter(ma.col("n").gt(0))

        collection = rel.collect_with_drift()

        assert collection.drifts == []
        with pytest.raises(ValueError, match="0 conform nodes"):
            collection.drift

    def test_effective_schema_reflects_actual_output_frame_under_evolve(self):
        """data_type='evolve' skips the cast -- the ACTUAL output column
        stays STRING even though the spec declares INTEGER. effective_schema
        must report the actual STRING, not the declared type (finding 5)."""
        df = pl.DataFrame({"n": ["1", "2"]})
        spec = TypeSpec(fields=[FieldSpec(name="n", type=U.INTEGER)], fields_match="open")
        rel = ma.relation(df).conform(spec, contract={"data_type": "evolve"})

        collection = rel.collect_with_drift()

        assert collection.frame["n"].dtype == pl.String
        assert collection.effective_schema["n"] == D.STRING
        assert collection.drift.type_mismatches[0].action == "evolve"

    def test_backend_override_accepted(self):
        df = pl.DataFrame({"n": [1, 2]})
        spec = TypeSpec(fields=[FieldSpec(name="n", type=U.INTEGER)])
        rel = ma.relation(df).conform(spec)

        collection = rel.collect_with_drift(backend="polars")

        assert collection.frame["n"].to_list() == [1, 2]


# ---------------------------------------------------------------------------
# Multi-conform ordering
# ---------------------------------------------------------------------------

class TestMultiConformOrdering:
    def _joined(self):
        # Each side carries one unmapped ("open" mode default) column with a
        # distinguishable name -- the resulting ConformDrift.extra_columns
        # entry lets the test tell left's drift apart from right's without
        # relying on resource_name/spec_name (both always None for a bare
        # Relation.conform() call).
        left = ma.relation(
            {"id": [1], "a": [1], "left_extra": [9]}
        ).conform(TypeSpec(fields=[
            FieldSpec(name="id", type=U.INTEGER), FieldSpec(name="a", type=U.INTEGER),
        ]))
        right = ma.relation(
            {"id": [1], "b": [2], "right_extra": [8]}
        ).conform(TypeSpec(fields=[
            FieldSpec(name="id", type=U.INTEGER), FieldSpec(name="b", type=U.INTEGER),
        ]))
        return left.join(right, on="id")

    def test_join_of_two_conformed_relations_two_drifts_in_traversal_order(self):
        collection = self._joined().collect_with_drift()

        assert len(collection.drifts) == 2
        assert collection.drifts[0].node_id == "conform:0"
        assert collection.drifts[1].node_id == "conform:1"
        # Left is visited before right (handlers.visit_join visits node.left
        # then node.right) -- traversal order, not just count.
        assert [c.name for c in collection.drifts[0].extra_columns] == ["left_extra"]
        assert [c.name for c in collection.drifts[1].extra_columns] == ["right_extra"]

    def test_drift_property_raises_for_multi_node_collection(self):
        collection = self._joined().collect_with_drift()

        with pytest.raises(ValueError, match="2 conform nodes"):
            collection.drift


# ---------------------------------------------------------------------------
# freeze fail-fast: first tripping node raises; err.drift carries its identity
# ---------------------------------------------------------------------------

class TestFreezeFailFast:
    def _joined_with_left_freeze(self):
        # Left: data_type="freeze" AND an actual unsafe mismatch -- trips.
        left_spec = TypeSpec(
            fields=[FieldSpec(name="id", type=U.INTEGER), FieldSpec(name="x", type=U.INTEGER)],
            fields_match="open",
            contract={"data_type": "freeze"},
        )
        left = ma.relation({"id": [1], "x": ["not-a-number"]}).conform(left_spec)

        # Right: no freeze, no mismatch -- must never be reached.
        right_spec = TypeSpec(
            fields=[FieldSpec(name="id", type=U.INTEGER), FieldSpec(name="y", type=U.INTEGER)],
        )
        right = ma.relation({"id": [1], "y": [2]}).conform(right_spec)

        return left.join(right, on="id")

    def test_to_polars_raises_from_first_tripping_node(self):
        joined = self._joined_with_left_freeze()

        with pytest.raises(SchemaDriftError) as exc_info:
            joined.to_polars()

        err = exc_info.value
        assert err.drift.node_id == "conform:0"
        assert err.drift.type_mismatches[0].name == "x"

    def test_collect_with_drift_raises_identically(self):
        """collect_with_drift shares the same execute-time visitor plumbing
        -- freeze still fails fast before a ConformCollection is built."""
        joined = self._joined_with_left_freeze()

        with pytest.raises(SchemaDriftError) as exc_info:
            joined.collect_with_drift()

        assert exc_info.value.drift.node_id == "conform:0"


# ---------------------------------------------------------------------------
# assess_drift() -- schema-only pre-flight, never raises
# ---------------------------------------------------------------------------

class TestAssessDrift:
    def test_no_conform_nodes_returns_empty_list(self):
        rel = ma.relation({"n": [1, 2]}).filter(ma.col("n").gt(0))
        assert rel.assess_drift() == []

    def test_single_conform_node_assessed(self):
        df = pl.DataFrame({"n": ["1", "2"]})
        spec = TypeSpec(fields=[FieldSpec(name="n", type=U.INTEGER)])
        rel = ma.relation(df).conform(spec)

        drifts = rel.assess_drift()

        assert len(drifts) == 1
        assert all(isinstance(d, ConformDrift) for d in drifts)

    def test_aggregates_across_two_conform_nodes(self):
        left = ma.relation({"id": [1], "a": [1]}).conform(
            TypeSpec(fields=[FieldSpec(name="id", type=U.INTEGER), FieldSpec(name="a", type=U.INTEGER)])
        )
        right = ma.relation({"id": [1], "b": [2]}).conform(
            TypeSpec(fields=[FieldSpec(name="id", type=U.INTEGER), FieldSpec(name="b", type=U.INTEGER)])
        )
        joined = left.join(right, on="id")

        drifts = joined.assess_drift()

        assert len(drifts) == 2

    def test_freeze_configured_node_is_reported_not_raised(self):
        """The core assess_drift guarantee: a freeze policy that WOULD raise
        at execute time is instead folded into the returned drift report."""
        spec = TypeSpec(
            fields=[FieldSpec(name="n", type=U.INTEGER)],
            fields_match="open",
            contract={"data_type": "freeze"},
        )
        rel = ma.relation({"n": ["not-a-number"]}).conform(spec)

        # Must not raise.
        drifts = rel.assess_drift()

        assert len(drifts) == 1
        mismatch = drifts[0].type_mismatches[0]
        assert mismatch.name == "n"
        assert mismatch.action == "freeze"

        # Confirm the same relation WOULD raise at execute time -- proving
        # assess_drift genuinely disabled policy enforcement, rather than
        # this contract never being freeze-worthy in the first place.
        with pytest.raises(SchemaDriftError):
            rel.to_polars()

    def test_never_executes_a_frame(self):
        """assess_drift must be pure AST introspection: it only ever calls
        schema-inspection methods, never an execute-oriented one
        (collect/to_polars/compile/...)."""
        accessed: list[str] = []

        class _WatchedFrame:
            def collect_schema(self):
                accessed.append("collect_schema")
                return pl.Schema({"n": pl.Int64})

            def __getattr__(self, name):
                accessed.append(name)
                raise AttributeError(name)

        spec = TypeSpec(fields=[FieldSpec(name="n", type=U.INTEGER)])
        rel = ma.relation(_WatchedFrame()).conform(spec)

        drifts = rel.assess_drift()

        assert len(drifts) == 1
        _EXECUTE_METHODS = {"collect", "to_polars", "to_native", "compile"}
        assert not (_EXECUTE_METHODS & set(accessed)), accessed
