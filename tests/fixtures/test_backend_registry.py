# tests/fixtures/test_backend_registry.py
"""Self-tests for the centralized backend registry."""
from __future__ import annotations
import datetime as dt
import subprocess
import sys
import textwrap
import polars as pl
import pandas as pd
import narwhals as nw
import ibis
import pytest

from .backend_registry import REGISTRY, ALL_BACKENDS, BackendSpec
from .backend_helpers import BackendResultHelper


SAMPLE = {"x": [1, 2, 3], "name": ["a", "b", "c"]}

# Regression fixture for item 112 / IB-DT-19: mixed null/non-null date AND
# datetime columns. ibis-sqlite used to crash constructing this shape at all
# (sqlite3.ProgrammingError on the pandas NaT a null value becomes during
# ibis's internal pandas-roundtrip staging) -- before any expression-level
# test, capability gate, or divergence fact ever ran.
NULL_TEMPORAL_DATA = {
    "id": [1, 2, 3],
    "when_date": [None, dt.date(2024, 1, 1), dt.date(2024, 1, 2)],
    "when_ts": [
        None,
        dt.datetime(2024, 1, 1, 12, 0, 0),
        dt.datetime(2024, 1, 2, 8, 30, 0),
    ],
}


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


def test_polars_lazy_registered():
    assert "polars-lazy" in REGISTRY
    spec = REGISTRY["polars-lazy"]
    assert spec.family == "polars-lazy"
    assert spec.materialization == "lazy"


def test_polars_lazy_build_returns_lazyframe():
    df = REGISTRY["polars-lazy"].build({"x": [1, 2, 3]}, table_name="sample")
    assert isinstance(df, pl.LazyFrame)


def test_polars_lazy_ordering_in_all_backends():
    # Convention: place polars-lazy right after polars for readability.
    idx = ALL_BACKENDS.index("polars")
    assert ALL_BACKENDS[idx + 1] == "polars-lazy"


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_build_survives_null_date_and_null_datetime(backend_name):
    """Regression for item 112 / IB-DT-19.

    Every backend must be able to construct a fixture with a null date value
    AND a null datetime value mixed with non-null rows -- independent of any
    expression-level test. ibis-sqlite is the backend this actually guards:
    it used to raise sqlite3.ProgrammingError building this shape at all.
    """
    df = REGISTRY[backend_name].build(NULL_TEMPORAL_DATA, table_name="null_temporal")
    assert BackendResultHelper.get_count(df, backend_name) == 3


# --- Upstream fix monitor (IB-DT-19) --------------------------------------
#
# The regression tests above prove Mountainash's OWN construction paths no
# longer crash -- but they do so via _sqlite_compat.ensure_sqlite_nat_adapter(),
# a process-global sqlite3 patch that, once installed anywhere in this test
# session, permanently masks the underlying ibis bug for every subsequent
# test in the same process. To detect when ibis fixes IB-DT-19 upstream, this
# probes bare `ibis.sqlite` in an isolated subprocess that never imports
# mountainash, so the adapter is never installed and ibis's own unpatched
# behaviour is what's actually observed.
_RAW_IBIS_SQLITE_NULL_TEMPORAL_SCRIPT = textwrap.dedent("""
    import datetime as dt
    import ibis

    data = {
        "id": [1, 2, 3],
        "when_date": [None, dt.date(2024, 1, 1), dt.date(2024, 1, 2)],
        "when_ts": [
            None,
            dt.datetime(2024, 1, 1, 12, 0, 0),
            dt.datetime(2024, 1, 2, 8, 30, 0),
        ],
    }
    conn = ibis.sqlite.connect(":memory:")
    t = conn.create_table("t", data, overwrite=True)
    assert t.count().execute() == 3
    print("OK")
""")


@pytest.mark.xfail(
    strict=True,
    reason=(
        "IB-DT-19 (registry/upstream-issues.yaml): raw ibis.sqlite stages "
        "in-memory tables via a pandas roundtrip and crashes binding a null "
        "date/timestamp value (sqlite3.ProgrammingError on NaTType). Isolated "
        "in a bare subprocess -- no mountainash import, so "
        "_sqlite_compat.ensure_sqlite_nat_adapter() is never installed -- to "
        "observe ibis's own unpatched behaviour. If this XPASSes, ibis fixed "
        "the NaT-binding bug upstream: update IB-DT-19 to closed in "
        "registry/upstream-issues.yaml and reassess whether "
        "ensure_sqlite_nat_adapter() is still needed."
    ),
)
def test_raw_ibis_sqlite_null_temporal_upstream_bug_ib_dt_19():
    result = subprocess.run(
        [sys.executable, "-c", _RAW_IBIS_SQLITE_NULL_TEMPORAL_SCRIPT],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
