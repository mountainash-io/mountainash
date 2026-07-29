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
