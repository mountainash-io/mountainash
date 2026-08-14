"""`_coerce_to_match` non-Polars-target coercion (item 94).

`UnifiedRelationVisitor._coerce_to_match(target, value)` only implements a
conversion ladder for `target is Polars` (LazyFrame/DataFrame). For every
other target family -- Narwhals, Ibis -- it silently falls through to a
bare `return value`, passing the raw, unconverted value straight into the
eventual join/join_asof call, which then fails with a confusing native
error from deep inside that backend's own compiler.

Design: mountainash-central 2026-08-14-coerce-to-match-non-polars-target-
design.md (Revision 3, 3 Codex adversarial review rounds -- APPROVED).
"""
from __future__ import annotations

import ibis
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from mountainash.relations.core.unified_visitor.relation_visitor import (
    UnifiedRelationVisitor,
)

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


def _nw_pandas(data: dict):
    return nw.from_native(pd.DataFrame(data), eager_only=True)


def _nw_polars(data: dict):
    return nw.from_native(pl.DataFrame(data), eager_only=True)


def _nw_pyarrow(data: dict):
    return nw.from_native(pa.table(data), eager_only=True)


IBIS_CONNECTORS = {
    "duckdb": lambda: ibis.duckdb.connect(),
    "polars": lambda: ibis.polars.connect(),
    "sqlite": lambda: ibis.sqlite.connect(":memory:"),
}


class TestIbisTargetDictAcceptance:
    """Item 94 acceptance test: confirmed live bug (design spec's
    'Empirical findings' section) -- an Ibis target + a raw dict right-hand
    value currently no-ops in `_coerce_to_match`, so the raw dict reaches
    Ibis's own join compiler and fails there with a confusing native
    error, never a clean, helpful `TypeError` from this codebase."""

    def test_join_coerces_dict_to_ibis_memtable_with_correct_data(self):
        con = ibis.duckdb.connect()
        left = con.create_table("t", {"id": [1, 2, 3], "a": ["x", "y", "z"]})
        right = {"id": [2, 3], "b": [10, 20]}

        result = (
            ma.relation(left)
            .join(right, on="id", how="inner")
            .sort("id")
            .to_polars()
        )
        assert result.to_dict(as_series=False) == {
            "id": [2, 3],
            "a": ["y", "z"],
            "b": [10, 20],
        }
