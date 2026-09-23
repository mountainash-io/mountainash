"""Relation backend error boundaries and materialization residue propagation."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)


def _nw(df: pl.DataFrame):
    import narwhals as nw
    return nw.from_native(df, eager_only=True)


class TestNarwhalsBackendLimitations:
    def test_narwhals_unnest_has_backend_owned_refusal(self):
        df = _nw(pl.DataFrame({"s": [{"a": 1}]}))
        rel = ma.relation(df).unnest("s", separator=".")
        with pytest.raises(BackendCapabilityError) as exc:
            rel.collect()
        error = exc.value
        assert error.backend == "narwhals"
        assert error.function_key is RKEY_MOUNTAINASH_REL.UNNEST
        assert error.limitation is None

    def test_narwhals_join_asof_tolerance_enriched(self):
        left = _nw(pl.DataFrame({"t": [1, 5], "v": [10, 20]}).sort("t"))
        right = _nw(pl.DataFrame({"t": [0], "r": [100]}).sort("t"))
        rel = ma.relation(left).join_asof(ma.relation(right), on="t", tolerance=2)
        with pytest.raises(BackendCapabilityError):
            rel.collect()




class TestDagMaterializeResidueDialectPropagation:
    """Backlog item 88: _compile_with_refs() previously constructed
    relation_system/expression_system with no dialect at all, so every
    DAG-path residue lookup returned empty regardless of which choke point
    was fixed. These exercise the real registry facts end-to-end through
    every DAG entry point."""

    def _nw_pandas(self, data: dict):
        import narwhals as nw
        return nw.from_native(pl.DataFrame(data).to_pandas(), eager_only=True)

    def _nw_polars(self, data: dict):
        import narwhals as nw
        return nw.from_native(pl.DataFrame(data), eager_only=True)

    def test_dag_collect_enriches_failure_on_dependency_ref(self):
        # NW-LIST-01 fails while materialising a DEPENDENCY ref ("derived"),
        # not the collect() target itself ("final", a harmless passthrough) --
        # proves the DAG's ref-materialisation loop is enriched too, not just
        # the final target compile.
        from mountainash.relations.dag import RelationDAG

        nwf = self._nw_pandas({"tags": [[1, 2, 3]]})
        dag = RelationDAG()
        dag.add("stg", ma.relation(nwf))
        dag.add(
            "derived",
            dag.ref("stg").select(ma.col("tags").list.contains(2).name.alias("r")),
        )
        dag.add("final", dag.ref("derived").select("r"))
        with pytest.raises(BackendCapabilityError) as exc_info:
            dag.collect("final")
        assert exc_info.value.limitation.upstream_ref == "NW-LIST-01"

    def test_dag_execute_enriches_adhoc_target(self):
        from mountainash.relations.dag import RelationDAG

        nwf = self._nw_pandas({"tags": [[1, 2, 3]]})
        dag = RelationDAG()
        rel = ma.relation(nwf).select(ma.col("tags").list.contains(2).name.alias("r"))
        with pytest.raises(BackendCapabilityError) as exc_info:
            dag.execute(rel)
        assert exc_info.value.limitation.upstream_ref == "NW-LIST-01"

    def test_dag_collect_with_drift_enriches_nw_list_04(self):
        # NW-LIST-04 (narwhals-polars, list.get negative index): confirmed
        # broken pre-fix even though standalone Relation.collect() already
        # worked for this fact -- proves the dialect-propagation fix, not
        # just the choke-point relocation.
        from mountainash.relations.dag import RelationDAG

        nwf = self._nw_polars({"a": [[1, 2, 3], [4, 5]]})
        dag = RelationDAG()
        dag.add("stg", ma.relation(nwf))
        dag.add(
            "derived",
            dag.ref("stg").select(ma.col("a").list.get(-1).name.alias("r")),
        )
        with pytest.raises(BackendCapabilityError) as exc_info:
            dag.collect_with_drift("derived")
        assert exc_info.value.limitation.upstream_ref == "NW-LIST-04"

    def test_dag_collect_enriches_string_split_on_dependency_under_differing_anchor_dialect(
        self,
    ):
        # Item 89 live-bug regression: NW-STR-22 (narwhals-pandas
        # str.split() requires a pyarrow-backed series) previously leaked
        # its raw native TypeError when the DAG's anchor dialect
        # (narwhals-polars, from "a_polars_src", alphabetically first and
        # therefore anchor) differed from the failing ref's own dialect
        # (narwhals-pandas, "b_pandas_derived") -- because the whole
        # compile call shared one visitor/expr_visitor pair scoped to
        # the anchor. The join target is never actually reached: the
        # failure is raised while compiling "b_pandas_derived" itself,
        # inside the per-ref materialisation loop, before the target's
        # own root.accept(visitor) runs -- isolating item 89's per-ref
        # dispatch fix from item 91's join/concat operand-coercion
        # concern.
        from mountainash.relations.dag import RelationDAG

        a_polars = self._nw_polars({"id": [1, 2]})
        b_pandas = self._nw_pandas({"id": [1, 2], "s": ["x,y", "p,q"]})
        dag = RelationDAG()
        dag.add("a_polars_src", ma.relation(a_polars))
        dag.add(
            "b_pandas_derived",
            ma.relation(b_pandas).select(
                ma.col("id"),
                ma.col("s").str.string_split(ma.lit(",")).name.alias("r"),
            ),
        )
        dag.add(
            "final",
            dag.ref("a_polars_src").join(dag.ref("b_pandas_derived"), on="id"),
        )
        with pytest.raises(BackendCapabilityError) as exc_info:
            dag.collect("final")
        assert exc_info.value.limitation.upstream_ref == "NW-STR-22"


def test_disjoint_finite_predicate_partition_gates_the_relation_visitor():
    """Concrete Polars scope: FETCH count is a native integer, not a family fallback."""
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityKey,
        CapabilityPolicyRule,
        CapabilitySegment,
        Domain,
        Selector,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import (
        Clause,
        ClauseOp,
        PolicyAction,
        PolicyConsumer,
        Predicate,
    )
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL

    scope = Scope(CONST_BACKEND.POLARS, Dialect("polars"))

    def policy(action, predicate, message):
        return CapabilityPolicyRule(
            key=CapabilityKey(
                RKEY_SUBSTRAIT_REL.FETCH,
                "count",
                Selector("predicate", predicate),
            ),
            level=(
                CapabilityLevel.UNSUPPORTED
                if action is PolicyAction.BLOCK
                else CapabilityLevel.EXPR_CAPABLE
            ),
            since="2026-09-18",
            message=message,
            consumer=PolicyConsumer.GATE,
            action=action,
        )

    permit_one = policy(
        PolicyAction.PERMIT,
        Predicate((Clause("count", ClauseOp.EQ, 1),)),
        "one row remains available",
    )
    block_remainder = policy(
        PolicyAction.BLOCK,
        Predicate((Clause("count", ClauseOp.IN, frozenset({2, 3})),)),
        "the selected finite remainder is unavailable",
    )
    segment = BoundSegment(
        "mountainash.relations.backends.capabilities.polars.dialects.polars.substrait.relation.finite_partition",
        scope,
        CapabilitySegment(Domain.RELATION, policies=(permit_one, block_remainder)),
    )
    snap = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        CapabilityRegistry.register_segment(segment)
        dataframe = pl.DataFrame({"value": [1, 2, 3]})
        assert ma.relation(dataframe).head(1).collect().to_dicts() == [{"value": 1}]
        with pytest.raises(BackendCapabilityError) as raised:
            ma.relation(dataframe).head(2).collect()
        assert raised.value.limitation.message == "the selected finite remainder is unavailable"
    finally:
        CapabilityRegistry.restore(snap)


@pytest.mark.parametrize("mode", ["checked", "trusted"])
def test_cold_relation_gate_obeys_request_policy(mode, monkeypatch):
    import mountainash as ma
    import polars as pl
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry, bootstrap
    from mountainash.core.capabilities.declarations import (
        BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.registry import _empty_state
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.types import BackendCapabilityError
    from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL

    declaration = BoundSegment(
        "mountainash.relations.backends.capabilities.polars.dialects.polars.substrait.relation.cold_gate",
        Scope(CONST_BACKEND.POLARS, Dialect("polars")),
        CapabilitySegment(Domain.RELATION, policies=(CapabilityPolicyRule(
            CapabilityKey(RKEY_SUBSTRAIT_REL.FETCH, "count"),
            CapabilityLevel.UNSUPPORTED, "2026-09-21", "controlled relation refusal",
            PolicyConsumer.GATE, PolicyAction.BLOCK,
        ),)),
    )
    def load_declarations():
        if mode == "trusted":
            raise RuntimeError("optional catalogue unavailable")
        return (declaration,)

    before = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.restore(_empty_state())  # UNINITIALIZED, not ISOLATED
        monkeypatch.setattr(bootstrap, "_load_segments", load_declarations)
        relation = ma.relation(pl.DataFrame({"value": [1, 2, 3]})).head(2)
        with ma.capability_policy(getattr(ma.CapabilityPolicy, mode)()):
            if mode == "checked":
                with pytest.raises(BackendCapabilityError) as error:
                    relation.collect()
                assert error.value.function_key is RKEY_SUBSTRAIT_REL.FETCH
                assert error.value.limitation.consumer is PolicyConsumer.GATE
            else:
                assert relation.collect().to_dicts() == [{"value": 1}, {"value": 2}]
    finally:
        CapabilityRegistry.restore(before)
