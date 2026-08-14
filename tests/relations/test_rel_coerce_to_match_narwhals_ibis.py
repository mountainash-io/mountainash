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


class TestNarwhalsTargetEagerDialects:
    """Design spec testing plan #1-3: dict/list[dict]/Polars-LazyFrame right-
    hand values against all 3 eager Narwhals target dialects. Every "join
    succeeds" assertion checks correct data AND the result's exact dialect
    matches the target -- not merely "doesn't raise" (directly defends
    against Revision 1's finding-2 regression, where a `dict` always became
    pandas-backed regardless of the target's actual dialect)."""

    @pytest.mark.parametrize(
        "target_factory,target_dialect",
        [
            (lambda: _nw_pandas({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-pandas"),
            (lambda: _nw_polars({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-polars"),
            (lambda: _nw_pyarrow({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-pyarrow"),
        ],
    )
    @pytest.mark.parametrize(
        "value_factory",
        [
            lambda: {"id": [2, 3], "b": [10, 20]},
            lambda: [{"id": 2, "b": 10}, {"id": 3, "b": 20}],
            lambda: pl.DataFrame({"id": [2, 3], "b": [10, 20]}).lazy(),
        ],
        ids=["dict", "list_of_dict", "polars_lazyframe"],
    )
    def test_join_matches_target_dialect_exactly(
        self, target_factory, target_dialect, value_factory
    ):
        from mountainash.core.backend_detection import narwhals_dialect

        target = target_factory()
        value = value_factory()
        coerced = UnifiedRelationVisitor._coerce_to_match(target, value)
        assert narwhals_dialect(coerced) == target_dialect
        rel = ma.relation(target).join(value, on="id", how="inner")
        result, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.dialect == target_dialect
        # Assert the compiled RESULT (not just the coerced operand) is a
        # narwhals frame of the target's exact dialect, then verify the
        # complete joined record set (id, a, b -- not just id, b).
        assert narwhals_dialect(result) == target_dialect
        d = result.to_dict(as_series=False)
        rows = sorted(zip(d["id"], d["a"], d["b"]))
        assert rows == [(2, "y", 10), (3, "z", 20)]


class TestIbisTableToNarwhalsTarget:
    """Design spec testing plan #4: an Ibis Table right-hand value against a
    Narwhals target materializes via .to_pyarrow() (the same duck-type
    pattern the pre-existing Polars branch already uses) then wraps -- this
    replaces Revision 1's incorrect rejection of Ibis-Table-to-Narwhals."""

    @pytest.mark.parametrize(
        "target_factory,target_dialect",
        [
            (lambda: _nw_pandas({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-pandas"),
            (lambda: _nw_polars({"id": [1, 2, 3], "a": ["x", "y", "z"]}), "narwhals-polars"),
        ],
    )
    def test_ibis_table_materializes_to_target_dialect(self, target_factory, target_dialect):
        from mountainash.core.backend_detection import narwhals_dialect

        target = target_factory()
        con = ibis.duckdb.connect()
        value = con.create_table("t", {"id": [2, 3], "b": [10, 20]})
        coerced = UnifiedRelationVisitor._coerce_to_match(target, value)
        assert narwhals_dialect(coerced) == target_dialect
        rel = ma.relation(target).join(value, on="id", how="inner")
        result, visitor = rel._compile_and_execute_with_visitor()
        assert visitor.backend.dialect == target_dialect
        assert narwhals_dialect(result) == target_dialect
        d = result.to_dict(as_series=False)
        rows = sorted(zip(d["id"], d["a"], d["b"]))
        assert rows == [(2, "y", 10), (3, "z", 20)]
