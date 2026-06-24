"""Conform on DURATION / YEAR / YEARMONTH — blocked pre-unification by the
incomplete type bridge. Cross-backend per testing-philosophy."""
import datetime

import polars as pl
import pytest

import mountainash as ma
from mountainash.typespec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS

# BACKENDS = ["polars", "pandas", "pyarrow"]


def _frame(backend, data):
    df = pl.DataFrame(data)
    if backend == "pandas":
        return df.to_pandas()
    if backend == "pyarrow":
        return df.to_arrow()
    return df


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_conform_duration(backend):
    df = _frame(backend, {"d": [1_000_000, 2_000_000]})
    spec = TypeSpec(fields=[FieldSpec(name="d", type=UniversalType.DURATION)])
    out = ma.relation(df).conform(spec).to_polars()
    assert out.schema["d"] == pl.Duration("us")


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_conform_year(backend):
    df = _frame(backend, {"y": [2024, 2025]})
    spec = TypeSpec(fields=[FieldSpec(name="y", type=UniversalType.YEAR)])
    out = ma.relation(df).conform(spec).to_polars()
    assert out.schema["y"] == pl.Int32


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_conform_yearmonth(backend):
    df = _frame(backend, {"ym": [202401, 202402]})
    spec = TypeSpec(fields=[FieldSpec(name="ym", type=UniversalType.YEARMONTH)])
    out = ma.relation(df).conform(spec).to_polars()
    assert out.schema["ym"] == pl.String


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_conform_any_skips_cast(backend):
    df = _frame(backend, {"a": [1, 2]})
    spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.ANY)])
    out = ma.relation(df).conform(spec).to_polars()
    assert out.schema["a"] == pl.Int64  # untouched
