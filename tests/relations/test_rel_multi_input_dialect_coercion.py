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
