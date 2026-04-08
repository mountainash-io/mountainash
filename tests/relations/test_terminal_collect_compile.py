"""Cross-backend contract tests for Relation.collect() and Relation.compile().

collect() MUST return a materialized native result for every backend.
compile() MUST return the native plan (lazy where the backend is lazy).
"""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.relations import relation


def test_collect_polars_lazyframe_returns_dataframe():
    """Regression guard: collect() on a LazyFrame source must NOT return a LazyFrame.

    Before this fix, `rel.collect()` leaked the LazyFrame and callers had to
    do `rel.collect().collect()`. That broke the one-syntax-all-backends promise.
    """
    lf = pl.DataFrame({"x": [1, 2, 3]}).lazy()
    result = relation(lf).collect()
    assert isinstance(result, pl.DataFrame)
    assert not isinstance(result, pl.LazyFrame)
    assert result.to_dicts() == [{"x": 1}, {"x": 2}, {"x": 3}]
