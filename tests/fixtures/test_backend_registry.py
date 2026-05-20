# tests/fixtures/test_backend_registry.py
"""Self-tests for the centralized backend registry."""
from __future__ import annotations
import polars as pl
import pandas as pd
import narwhals as nw
import ibis
import pytest

from .backend_registry import REGISTRY, ALL_BACKENDS, BackendSpec


SAMPLE = {"x": [1, 2, 3], "name": ["a", "b", "c"]}


def test_registry_has_expected_backends():
    expected = {
        "polars", "pandas",
        "narwhals-polars", "narwhals-pandas",
        "ibis-polars", "ibis-sqlite", "ibis-duckdb",
        # polars-lazy is added in a later task (Task 6) — not yet present
    }
    assert expected.issubset(set(REGISTRY.keys()))


def test_all_backends_is_keys_of_registry_in_order():
    # ALL_BACKENDS excludes legacy aliases (e.g. "narwhals") that exist in
    # REGISTRY for backward-compat with tests that hardcode them in @parametrize.
    # Verify: every ALL_BACKENDS entry is in REGISTRY, in the same relative order.
    registry_keys = [k for k in REGISTRY if k in set(ALL_BACKENDS)]
    assert ALL_BACKENDS == registry_keys


@pytest.mark.parametrize("backend_name", [
    "polars", "pandas",
    "narwhals-polars", "narwhals-pandas",
    "ibis-polars", "ibis-sqlite", "ibis-duckdb",
])
def test_build_returns_native_object(backend_name):
    df = REGISTRY[backend_name].build(SAMPLE, table_name="sample")
    assert df is not None


def test_polars_build_returns_dataframe():
    df = REGISTRY["polars"].build(SAMPLE, table_name="sample")
    assert isinstance(df, pl.DataFrame)


def test_pandas_build_returns_dataframe():
    df = REGISTRY["pandas"].build(SAMPLE, table_name="sample")
    assert isinstance(df, pd.DataFrame)


def test_narwhals_polars_build_returns_narwhals_frame():
    df = REGISTRY["narwhals-polars"].build(SAMPLE, table_name="sample")
    # narwhals wraps the native; .to_native() returns the underlying polars
    assert isinstance(df.to_native(), pl.DataFrame)


def test_narwhals_pandas_build_returns_narwhals_frame():
    df = REGISTRY["narwhals-pandas"].build(SAMPLE, table_name="sample")
    assert isinstance(df.to_native(), pd.DataFrame)


@pytest.mark.parametrize("backend_name", ["ibis-polars", "ibis-sqlite", "ibis-duckdb"])
def test_ibis_build_returns_table(backend_name):
    t = REGISTRY[backend_name].build(SAMPLE, table_name="sample")
    assert isinstance(t, ibis.expr.types.Table)


def test_spec_family_and_materialization_present():
    for name, spec in REGISTRY.items():
        assert isinstance(spec, BackendSpec)
        assert spec.family in {"polars-eager", "polars-lazy", "pandas", "narwhals", "ibis"}
        assert spec.materialization in {"eager", "lazy", "deferred"}


def test_eager_backends_have_eager_materialization():
    for name in ["polars", "pandas", "narwhals-polars", "narwhals-pandas"]:
        assert REGISTRY[name].materialization == "eager"


def test_ibis_backends_have_deferred_materialization():
    for name in ["ibis-polars", "ibis-sqlite", "ibis-duckdb"]:
        assert REGISTRY[name].materialization == "deferred"
