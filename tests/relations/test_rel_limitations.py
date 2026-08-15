"""Relation limitations registry: seeds + structural enrichment (spec §3.8)."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError


def _nw(df: pl.DataFrame):
    import narwhals as nw
    return nw.from_native(df, eager_only=True)


class TestSeededNarwhalsLimitations:
    def test_narwhals_unnest_enriched(self):
        df = _nw(pl.DataFrame({"s": [{"a": 1}]}))
        rel = ma.relation(df).unnest("s", separator=".")
        with pytest.raises(BackendCapabilityError) as exc:
            rel.collect()
        assert exc.value.limitation is not None
        assert "unnest" in str(exc.value).lower() or exc.value.limitation.message

    def test_narwhals_join_asof_tolerance_enriched(self):
        left = _nw(pl.DataFrame({"t": [1, 5], "v": [10, 20]}).sort("t"))
        right = _nw(pl.DataFrame({"t": [0], "r": [100]}).sort("t"))
        rel = ma.relation(left).join_asof(ma.relation(right), on="t", tolerance=2)
        with pytest.raises(BackendCapabilityError):
            rel.collect()


class TestStructuralInvariant:
    def test_base_mixin_shape(self):
        from mountainash.relations.backends.relation_systems.base import (
            BaseRelationSystem,
        )
        # The legacy KNOWN_REL_LIMITATIONS dict was retired in the spine's
        # Phase 1 (its absence is guarded by test_no_legacy_registries_remain).
        assert not hasattr(BaseRelationSystem, "KNOWN_REL_LIMITATIONS")
        assert BaseRelationSystem.BACKEND_NAME == "unknown"

    def test_all_backends_carry_backend_name(self):
        from mountainash.relations.backends.relation_systems.polars import (
            PolarsRelationSystem,
        )
        assert PolarsRelationSystem.BACKEND_NAME == "polars"


@pytest.fixture
def _polars_materialize_residue():
    """Register an isolated MATERIALIZE-boundary CapabilityFact for polars so
    a native ColumnNotFoundError at collect enriches to BackendCapabilityError.

    Residue is matched by native exception type (registry.residue_for), so the
    carrier op key (UNNEST, unused by these plans) is irrelevant to the match —
    it only has to be a real registered relation op for registration to
    validate. snapshot/restore keeps the fact out of every other test.
    """
    from mountainash.core.capabilities import (
        Boundary,
        CapabilityFact,
        CapabilityLevel,
        CapabilityRegistry,
        Enforcement,
    )
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_MOUNTAINASH_REL,
    )

    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.register_backend(
            CONST_BACKEND.POLARS,
            [
                CapabilityFact(
                    operation_key=RKEY_MOUNTAINASH_REL.UNNEST,
                    param="*",
                    level=CapabilityLevel.UNSUPPORTED,
                    backend=CONST_BACKEND.POLARS,
                    message="materialize-time quirk",
                    enforcement=Enforcement.MATERIALIZE_RESIDUE,
                    boundary=Boundary.MATERIALIZE,
                    native_errors=(pl.exceptions.ColumnNotFoundError,),
                    since="2026-07-05",
                )
            ],
        )
        yield
    finally:
        CapabilityRegistry.restore(snap)


class TestMaterializeBoundary:
    def test_materialize_failures_consult_boundary_entries(
        self, _polars_materialize_residue
    ):
        rel = ma.relation(pl.DataFrame({"a": [1]}).lazy()).filter(
            ma.col("missing") > 0
        )
        with pytest.raises(BackendCapabilityError, match="materialize-time quirk"):
            rel.collect()

    def test_dag_collect_with_drift_consults_boundary_entries(
        self, _polars_materialize_residue
    ):
        from mountainash.relations.dag import RelationDAG

        dag = RelationDAG()
        dag.add(
            "bad",
            ma.relation(pl.DataFrame({"a": [1]}).lazy()).filter(
                ma.col("missing") > 0
            ),
        )
        with pytest.raises(BackendCapabilityError, match="materialize-time quirk"):
            dag.collect_with_drift("bad")


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


def test_predicate_fact_gates_relation_call():
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.schema import (
        CapabilityFact, CapabilityLevel, Clause, ClauseOp, Predicate,
    )
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL

    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, [
            CapabilityFact(
                operation_key=RKEY_SUBSTRAIT_REL.FILTER, param="predicate",
                level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.NARWHALS,
                message="filter blocked by predicate fact", since="2026-08-15",
                predicate=Predicate((Clause("predicate", ClauseOp.IS_SET),)),
            ),
        ])
        df = _nw(pl.DataFrame({"a": [1, 2]}))
        with pytest.raises(BackendCapabilityError, match="filter blocked"):
            ma.relation(df).filter(ma.col("a").eq(1)).collect()
    finally:
        CapabilityRegistry.restore(snap)
