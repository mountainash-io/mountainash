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
