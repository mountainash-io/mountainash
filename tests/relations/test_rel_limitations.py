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
        assert BaseRelationSystem.KNOWN_REL_LIMITATIONS == {}
        assert BaseRelationSystem.BACKEND_NAME == "unknown"

    def test_all_backends_carry_backend_name(self):
        from mountainash.relations.backends.relation_systems.polars import (
            PolarsRelationSystem,
        )
        assert PolarsRelationSystem.BACKEND_NAME == "polars"


class TestMaterializeBoundary:
    def test_materialize_failures_consult_boundary_entries(self, monkeypatch):
        from mountainash.core.limitations import MATERIALIZE_BOUNDARY, WILDCARD_PARAM
        from mountainash.core.types import KnownLimitation
        from mountainash.relations.backends.relation_systems.polars import (
            PolarsRelationSystem,
        )

        monkeypatch.setattr(
            PolarsRelationSystem,
            "KNOWN_REL_LIMITATIONS",
            {
                (MATERIALIZE_BOUNDARY, WILDCARD_PARAM): KnownLimitation(
                    message="materialize-time quirk",
                    native_errors=(pl.exceptions.ColumnNotFoundError,),
                )
            },
            raising=False,
        )
        rel = ma.relation(pl.DataFrame({"a": [1]}).lazy()).filter(
            ma.col("missing") > 0
        )
        with pytest.raises(BackendCapabilityError, match="materialize-time quirk"):
            rel.collect()

    def test_dag_collect_with_drift_consults_boundary_entries(self, monkeypatch):
        from mountainash.core.limitations import MATERIALIZE_BOUNDARY, WILDCARD_PARAM
        from mountainash.core.types import KnownLimitation
        from mountainash.relations.backends.relation_systems.polars import (
            PolarsRelationSystem,
        )
        from mountainash.relations.dag import RelationDAG

        monkeypatch.setattr(
            PolarsRelationSystem,
            "KNOWN_REL_LIMITATIONS",
            {
                (MATERIALIZE_BOUNDARY, WILDCARD_PARAM): KnownLimitation(
                    message="materialize-time quirk",
                    native_errors=(pl.exceptions.ColumnNotFoundError,),
                )
            },
            raising=False,
        )
        dag = RelationDAG()
        dag.add(
            "bad",
            ma.relation(pl.DataFrame({"a": [1]}).lazy()).filter(
                ma.col("missing") > 0
            ),
        )
        with pytest.raises(BackendCapabilityError, match="materialize-time quirk"):
            dag.collect_with_drift("bad")
