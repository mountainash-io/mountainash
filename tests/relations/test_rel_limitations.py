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
