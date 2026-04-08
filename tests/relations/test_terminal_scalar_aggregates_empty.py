"""Empty-relation behaviour for scalar aggregate terminals."""
from __future__ import annotations

import polars as pl

import mountainash as ma
from mountainash.relations import relation


def _empty_rel():
    df = pl.DataFrame({"x": [1, 2, 3]})
    return relation(df).filter(ma.col("x").gt(ma.lit(999)))


def test_empty_sum_returns_null_or_zero():
    """Empty input -> Substrait sum yields null. Polars represents this as None."""
    result = _empty_rel().sum("x")
    assert result is None or result == 0


def test_empty_avg_returns_null():
    result = _empty_rel().avg("x")
    assert result is None


def test_empty_min_returns_null():
    result = _empty_rel().min("x")
    assert result is None


def test_empty_max_returns_null():
    result = _empty_rel().max("x")
    assert result is None
