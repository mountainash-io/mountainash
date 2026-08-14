"""Multi-input relation node cross-dialect coercion (item 91).

A single relation tree combining two same-family, different-native-dialect
Narwhals operands (e.g. narwhals-pandas joined against narwhals-polars)
never reached cross-type-joins.md's documented coercion path -- narwhals'
own read() never raises for a cross-dialect wrap, so the existing
_visit_and_coerce_right except-TypeError trigger never fired; the raw
TypeError actually surfaces one level up, inside visitor.backend.join()/
nw.concat(), outside any existing exception handling.

Design: mountainash-central 2026-08-13-relation-visitor-multi-input-
dialect-coercion-design.md (Revision 4, 4 Codex adversarial review rounds).
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.constants import CONST_BACKEND

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


def _nw_pandas(data: dict):
    import narwhals as nw
    import pandas as pd
    return nw.from_native(pd.DataFrame(data), eager_only=True)


def _nw_polars(data: dict):
    import narwhals as nw
    import polars as pl
    return nw.from_native(pl.DataFrame(data), eager_only=True)


def _nw_pyarrow(data: dict):
    import narwhals as nw
    import pyarrow as pa
    return nw.from_native(pa.table(data), eager_only=True)


class TestMultiInputCrossDialectCoercionAcceptance:
    """Item 91 acceptance test: confirmed live bug (design spec's
    'Empirical findings' section)."""

    def test_join_coerces_narwhals_dialect_mismatch_with_correct_data(self):
        left = _nw_pandas({"id": [1, 2], "a": ["x", "y"]})
        right = _nw_polars({"id": [2, 3], "b": [10, 20]})
        rel = ma.relation(left).join(right, on="id")
        result = rel.collect()
        assert result.to_dict(orient="list") == {"id": [2], "a": ["y"], "b": [10]}

    def test_join_reversed_coerces_right_to_left_polars_authoritative(self):
        left = _nw_polars({"id": [1, 2], "a": [10, 20]})
        right = _nw_pandas({"id": [2, 3], "b": ["x", "y"]})
        rel = ma.relation(left).join(right, on="id")
        result_visitor = rel._compile_and_execute_with_visitor()
        result, visitor = result_visitor
        assert visitor.backend.dialect == "narwhals-polars"
        assert result.to_dict(as_series=False) == {"id": [2], "a": [20], "b": ["x"]}

    def test_join_asof_coerces_narwhals_dialect_mismatch(self):
        left = _nw_pandas({"id": [1, 3, 5], "a": ["x", "y", "z"]})
        right = _nw_polars({"id": [1, 2, 4], "b": [10, 20, 30]})
        rel = ma.relation(left).join_asof(right, on="id", strategy="backward")
        result = rel.collect()
        assert result.to_dict(orient="list") == {
            "id": [1, 3, 5],
            "a": ["x", "y", "z"],
            "b": [10, 20, 30],
        }


class TestEagerLazyShapeCoercion:
    """Design spec testing plan #7 -- Revision 4's fix for round-3's
    finding: narwhals_dialect() only special-cases eager/lazy for the
    `polars` implementation, so eager-pandas vs lazy-pandas (and
    eager-pyarrow vs lazy-pyarrow) share an IDENTICAL dialect string.
    Coercion must detect the shape mismatch via an independent eager/lazy
    check, not dialect-string equality alone."""

    def test_eager_polars_target_collects_lazy_polars_value(self):
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        import narwhals as nw
        import polars as pl

        target = _nw_polars({"id": [1, 2]})
        value = nw.from_native(pl.DataFrame({"id": [1, 2]}).lazy())
        coerced = UnifiedRelationVisitor._coerce_same_family_dialect(target, value)
        assert not is_narwhals_lazy(coerced)
        assert coerced.to_native().to_dict(as_series=False) == {"id": [1, 2]}

    def test_eager_pandas_target_collects_lazy_pandas_value(self):
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )

        target = _nw_pandas({"id": [1, 2]})
        value = _nw_pandas({"id": [1, 2]}).lazy()
        coerced = UnifiedRelationVisitor._coerce_same_family_dialect(target, value)
        assert not is_narwhals_lazy(coerced)
        assert coerced.to_native().to_dict(orient="list") == {"id": [1, 2]}

    def test_eager_pyarrow_target_collects_lazy_pyarrow_value(self):
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )

        target = _nw_pyarrow({"id": [1, 2]})
        value = _nw_pyarrow({"id": [1, 2]}).lazy()
        coerced = UnifiedRelationVisitor._coerce_same_family_dialect(target, value)
        assert not is_narwhals_lazy(coerced)

    def test_lazy_polars_target_rejects_eager_operand(self):
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        import narwhals as nw
        import polars as pl

        target = nw.from_native(pl.DataFrame({"id": [1]}).lazy())
        value = _nw_pandas({"id": [1]})
        with pytest.raises(TypeError, match="lazy"):
            UnifiedRelationVisitor._coerce_same_family_dialect(target, value)

    def test_lazy_pandas_target_rejects_eager_operand(self):
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )

        target = _nw_pandas({"id": [1]}).lazy()
        value = _nw_polars({"id": [1]})
        with pytest.raises(TypeError, match="lazy"):
            UnifiedRelationVisitor._coerce_same_family_dialect(target, value)

    def test_lazy_value_needing_conversion_after_collect(self):
        """lazy-Polars value -> collect -> eager-Polars -> convert to
        pandas target (design spec testing plan #7, third bullet)."""
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        import narwhals as nw
        import polars as pl

        target = _nw_pandas({"id": [1, 2]})
        value = nw.from_native(pl.DataFrame({"id": [1, 2]}).lazy())
        coerced = UnifiedRelationVisitor._coerce_same_family_dialect(target, value)
        from mountainash.core.backend_detection import narwhals_dialect
        assert narwhals_dialect(coerced) == "narwhals-pandas"


def is_narwhals_lazy(frame) -> bool:
    from mountainash.core.types import is_narwhals_lazyframe
    return is_narwhals_lazyframe(frame)


class TestRefRelNodeAndAdhocExecuteOperandCoverage:
    """Design spec testing plan #5-6: RefRelNode (DAG-resolved) operands,
    and an ad-hoc execute() tree combining a direct ReadRelNode with a
    RefRelNode of a different dialect, both operand orderings. Verifies
    the coercion fix's central design claim -- it operates on the
    VISITED result, so it needs no special-casing for where an operand
    came from."""

    def test_two_named_refs_different_dialects_collect_correctly(self):
        from mountainash.relations.dag import RelationDAG

        dag = RelationDAG()
        dag.add("nw_pandas_src", ma.relation(_nw_pandas({"id": [1, 2], "a": ["x", "y"]})))
        dag.add("nw_polars_src", ma.relation(_nw_polars({"id": [2, 3], "b": [10, 20]})))
        dag.add("joined", dag.ref("nw_pandas_src").join(dag.ref("nw_polars_src"), on="id"))
        result = dag.collect("joined")
        # dag.collect() returns the narwhals-wrapped result as-is (unlike
        # Relation.collect()'s unwrap=True default) -- narwhals' own
        # .to_dict(as_series=False) mirrors Polars' API surface uniformly
        # regardless of the underlying native backend, so this assertion
        # doesn't need to know or assume which dialect the anchor resolved
        # to.
        assert result.to_dict(as_series=False) == {"id": [2], "a": ["y"], "b": [10]}

    def test_adhoc_execute_ref_left_local_right(self):
        from mountainash.relations.dag import RelationDAG

        dag = RelationDAG()
        dag.add("nw_pandas_src", ma.relation(_nw_pandas({"id": [1, 2], "a": ["x", "y"]})))
        local_polars_df = _nw_polars({"id": [2, 3], "b": [10, 20]})
        target = dag.ref("nw_pandas_src").join(local_polars_df, on="id")
        result = dag.execute(target)
        assert result.to_dict(as_series=False) == {"id": [2], "a": ["y"], "b": [10]}

    def test_adhoc_execute_local_left_ref_right(self):
        from mountainash.relations.dag import RelationDAG

        dag = RelationDAG()
        dag.add("nw_pandas_src", ma.relation(_nw_pandas({"id": [1, 2], "a": ["x", "y"]})))
        local_polars_rel = ma.relation(_nw_polars({"id": [2, 3], "b": [10, 20]}))
        target = local_polars_rel.join(dag.ref("nw_pandas_src"), on="id")
        result = dag.execute(target)
        assert result.to_dict(as_series=False) == {"id": [2], "b": [10], "a": ["y"]}


class TestUnionMultiWayDialectCoercion:
    """Design spec testing plan #4: 3-way mix of pandas/polars/pyarrow
    narwhals dialects via union_all/union_distinct; inputs[0]'s dialect
    wins (left-authoritative, matching join's convention); narwhals'
    raw failure mode for a pandas+PyArrow pair is AttributeError, not
    TypeError -- this coercion is proactive/identity-based and never
    depends on narwhals' exception type, proven explicitly here."""

    def test_union_all_three_way_dialect_mix_pandas_anchor(self):
        a = ma.relation(_nw_pandas({"id": [1], "v": ["a"]}))
        b = ma.relation(_nw_polars({"id": [2], "v": ["b"]}))
        c = ma.relation(_nw_pyarrow({"id": [3], "v": ["c"]}))
        result = ma.concat([a, b, c]).collect()
        assert sorted(result.to_dict(orient="list")["id"]) == [1, 2, 3]
        assert sorted(result.to_dict(orient="list")["v"]) == ["a", "b", "c"]

    def test_union_all_pandas_pyarrow_pair_succeeds_despite_attributeerror_native_mode(self):
        """narwhals' raw nw.concat([pandas, pyarrow]) raises AttributeError
        (not TypeError) -- confirmed in the design spec's empirical
        findings. This coercion never relies on catching that native
        exception (it's proactive), so it must succeed regardless."""
        a = ma.relation(_nw_pandas({"id": [1], "v": ["a"]}))
        c = ma.relation(_nw_pyarrow({"id": [2], "v": ["b"]}))
        result = ma.concat([a, c]).collect()
        assert sorted(result.to_dict(orient="list")["id"]) == [1, 2]

    def test_union_distinct_dedups_across_dialects(self):
        a = ma.relation(_nw_pandas({"id": [1, 2], "v": ["a", "b"]}))
        b = ma.relation(_nw_polars({"id": [2, 3], "v": ["b", "c"]}))
        result = ma.concat([a, b], distinct=True).collect()
        rows = sorted(zip(result.to_dict(orient="list")["id"], result.to_dict(orient="list")["v"]))
        assert rows == [(1, "a"), (2, "b"), (3, "c")]


class TestUnsupportedDialectAndErrorWrapping:
    """Design spec testing plan #8-9."""

    def test_unrecognized_target_implementation_raises_clean_typeerror(self):
        from enum import Enum
        from unittest.mock import patch
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )

        class _UnknownImpl(Enum):
            UNKNOWN = "unknown"

        target = _nw_pandas({"id": [1]})
        value = _nw_polars({"id": [1]})
        with patch.object(target, "implementation", _UnknownImpl.UNKNOWN):
            with pytest.raises(TypeError, match="unsupported target dialect"):
                UnifiedRelationVisitor._coerce_same_family_dialect(target, value)

    def test_conversion_failure_is_wrapped_with_dialect_context_not_leaked_raw(self):
        from unittest.mock import patch
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        import narwhals as nw

        target = _nw_pandas({"id": [1]})
        value = _nw_polars({"id": [1]})
        frame_type = type(value)
        original_to_pandas = frame_type.to_pandas

        def _boom(self):
            raise TypeError("conversion exploded")

        try:
            frame_type.to_pandas = _boom
            with pytest.raises(TypeError, match="Failed to coerce"):
                UnifiedRelationVisitor._coerce_same_family_dialect(target, value)
        finally:
            frame_type.to_pandas = original_to_pandas

    def test_same_dialect_operands_untouched_no_wasted_round_trip(self):
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )

        target = _nw_pandas({"id": [1]})
        value = _nw_pandas({"id": [2]})
        result = UnifiedRelationVisitor._coerce_same_family_dialect(target, value)
        assert result is value
        assert result.to_native() is value.to_native()


class TestExhaustiveLeafWalkRegressionSafety:
    """Design spec testing plan #11 (backlog Required work #4). Both
    _find_leaf_read_node and _find_leaf_backend currently recurse into
    children()[0] only -- a RefRelNode in a non-first position is
    invisible to standalone backend detection until visit_ref's own
    RelationDAGRequired safety net fires later, during actual node
    visiting, by which point the first child may have already been
    partially compiled."""

    def test_ref_in_second_position_raises_before_first_child_compiles(self):
        from unittest.mock import patch
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )
        from mountainash.relations.dag.errors import RelationDAGRequired

        left = ma.relation(_nw_pandas({"id": [1]}))
        target = left.join(ma.relation(_nw_pandas({"id": [1]})), on="id")
        # Replace the right side with an unregistered RefRelNode after
        # construction, simulating "ref in second position" without
        # needing a live DAG (this item's fix must reject it standalone).
        from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
        target_node = target._node.model_copy(
            update={"right": RefRelNode(name="missing_ref")}
        )
        target = type(target)(target_node)

        original_init = UnifiedRelationVisitor.__init__
        construction_count = [0]

        def _counted_init(self, *args, **kwargs):
            construction_count[0] += 1
            return original_init(self, *args, **kwargs)

        with patch.object(UnifiedRelationVisitor, "__init__", _counted_init):
            with pytest.raises(RelationDAGRequired):
                target._compile_and_execute()
        assert construction_count[0] == 0

    def test_readrelnode_in_first_position_still_wins_over_leafless_second_child(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ResourceReadRelNode,
        )
        from mountainash.typespec.datapackage import DataResource

        import polars as pl
        left = ma.relation(pl.DataFrame({"id": [1], "a": [1]}))
        resource = ResourceReadRelNode(
            resource=DataResource(name="right", data=[{"id": 1, "b": 2}])
        )
        target_node = left.join(left, on="id")._node.model_copy(
            update={"right": resource}
        )
        target = type(left)(target_node)
        # Detection must still find the left ReadRelNode leaf and pick
        # Polars -- the leaf-less second child must not abort detection.
        detected = target._detect_backend_from(target_node)
        assert detected == CONST_BACKEND.POLARS

    def test_all_children_leafless_falls_through_to_house_default_backend(self):
        """Round-3 non-blocking suggestion #1: explicit, documented
        coverage for the all-branches-unrecognizable case -- neither
        child produces a leaf, detection returns None, and
        _detect_backend_from's own existing fallback chain (not new
        leniency invented by this item) defaults to POLARS."""
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ResourceReadRelNode,
        )
        from mountainash.typespec.datapackage import DataResource

        resource_a = ResourceReadRelNode(
            resource=DataResource(name="a", data=[{"id": 1, "x": 1}])
        )
        resource_b = ResourceReadRelNode(
            resource=DataResource(name="b", data=[{"id": 1, "y": 2}])
        )
        placeholder = ma.relation(_nw_polars({"id": [1]}))
        target_node = placeholder.join(placeholder, on="id")._node.model_copy(
            update={"left": resource_a, "right": resource_b}
        )
        target = type(placeholder)(target_node)
        detected = target._detect_backend_from(target_node)
        assert detected == CONST_BACKEND.POLARS


@pytest.fixture
def _narwhals_pandas_join_gate_fact():
    """Register an isolated, dialect-scoped GATE fact: JOIN is
    UNSUPPORTED on narwhals-pandas specifically (test-only, not a real
    production limitation) -- used to prove item 91 testing plan #10: the
    compiling visitor gates using the ANCHOR's dialect, not a
    JoinRelNode's true left-operand dialect. Item 95's scope to fix, not
    this item's."""
    from mountainash.core.capabilities import (
        CapabilityFact,
        CapabilityLevel,
        CapabilityRegistry,
        Enforcement,
        WILDCARD_PARAM,
    )
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_SUBSTRAIT_REL,
    )

    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.register_backend(
            CONST_BACKEND.NARWHALS,
            [
                CapabilityFact(
                    operation_key=RKEY_SUBSTRAIT_REL.JOIN,
                    param=WILDCARD_PARAM,
                    level=CapabilityLevel.UNSUPPORTED,
                    backend=CONST_BACKEND.NARWHALS,
                    dialect="narwhals-pandas",
                    message="test-only GATE for narwhals-pandas join (item 91 testing plan #10)",
                    enforcement=Enforcement.GATE,
                    since="2026-08-13",
                )
            ],
        )
        yield
    finally:
        CapabilityRegistry.restore(snap)


class TestGatingUsesAnchorDialectNotTrueLeftOperandDialect:
    """Design spec testing plan #10 (required per Codex's suggested
    resolution for round-1 finding #2 -- this item ships the fix, item 95
    ships the gating-precision fix, sequenced after). Pins the current,
    known-limited behaviour with a REAL dialect-scoped CapabilityFact,
    not merely an inspection of visitor.backend.dialect."""

    def test_pandas_scoped_join_gate_does_not_fire_when_anchor_is_polars(
        self, _narwhals_pandas_join_gate_fact
    ):
        from mountainash.relations.dag import RelationDAG

        dag = RelationDAG()
        # "a_polars_src" sorts alphabetically first -> becomes the anchor
        # (RelationDAG._execute_with_visitor's own documented selection:
        # sorted(all_refs)[0]) -- regardless of tree position.
        dag.add("a_polars_src", ma.relation(_nw_polars({"id": [1], "x": [1]})))
        dag.add("z_pandas_src", ma.relation(_nw_pandas({"id": [1], "y": [1]})))
        # The join's TRUE left/authoritative operand is "z_pandas_src"
        # (narwhals-pandas) -- exactly what the registered GATE fact
        # targets.
        joined = dag.ref("z_pandas_src").join(dag.ref("a_polars_src"), on="id")

        result, visitor = dag._execute_with_visitor(joined)

        # Pins the current, documented limitation (item 95's charter):
        # the anchor is narwhals-polars, NOT the join's true left operand
        # (narwhals-pandas) -- so the pandas-scoped GATE fact never fires,
        # even though a fully operand-aware gate SHOULD have blocked this
        # join. The join succeeds anyway (coercion, Task 3, still works
        # correctly regardless of gating precision).
        assert visitor.backend.dialect == "narwhals-polars"
        assert result is not None
