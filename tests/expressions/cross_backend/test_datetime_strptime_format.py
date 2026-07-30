"""Cross-backend behaviour for strptime `format` (spec 2026-07-28 section 3, PR-B)."""
from __future__ import annotations

import datetime as _dt

import pytest

import mountainash as ma
from mountainash.core.capabilities import load_all_capability_declarations
from mountainash.core.types import BackendCapabilityError

load_all_capability_declarations()

STRPTIME_BACKENDS = [
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
    "narwhals-lazy",
    "pandas",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
]

# narwhals-pandas and the raw pandas fixture (which the backend-detection layer
# resolves to the `narwhals-pandas` dialect) cannot do str.to_date — upstream
# returns an object-dtype Series.  ibis-sqlite has no compilation rule for
# StringToDate/StringToTimestamp.  All three are covered by the dedicated gate
# tests in this file rather than re-failing here under a value assertion.
TO_DATE_HONORING_BACKENDS = [
    b for b in STRPTIME_BACKENDS
    if b not in ("ibis-sqlite", "narwhals-pandas", "pandas")
]
# ibis-sqlite is the only dialect declared UNSUPPORTED for str.to_datetime.
TO_DATETIME_HONORING_BACKENDS = [
    b for b in STRPTIME_BACKENDS if b != "ibis-sqlite"
]

# Ambiguous input: "2024-01-05" parses cleanly under BOTH formats and yields
# different dates, so the probe discriminates without relying on a parse error.
_DATA = {"s": ["2024-01-05", "2024-02-03", "2024-03-11"]}
_DT_DATA = {"s": ["2024-01-05 06:07:08", "2024-02-03 09:10:11", "2024-03-11 12:13:14"]}

_ISO_DATES = [_dt.date(2024, 1, 5), _dt.date(2024, 2, 3), _dt.date(2024, 3, 11)]
_SWAPPED_DATES = [_dt.date(2024, 5, 1), _dt.date(2024, 3, 2), _dt.date(2024, 11, 3)]


@pytest.mark.parametrize("backend_name", TO_DATE_HONORING_BACKENDS)
@pytest.mark.parametrize(
    ("fmt", "expected"),
    [("%Y-%m-%d", _ISO_DATES), ("%Y-%d-%m", _SWAPPED_DATES)],
)
def test_to_date_honors_format(backend_name, fmt, expected, backend_factory, collect_expr) -> None:
    df = backend_factory.create(_DATA, backend_name)
    got = collect_expr(df, ma.col("s").str.to_date(fmt))
    assert got == expected


@pytest.mark.parametrize("backend_name", TO_DATETIME_HONORING_BACKENDS)
@pytest.mark.parametrize(
    ("fmt", "expected"),
    [
        ("%Y-%m-%d %H:%M:%S", [_dt.datetime(2024, 1, 5, 6, 7, 8), _dt.datetime(2024, 2, 3, 9, 10, 11), _dt.datetime(2024, 3, 11, 12, 13, 14)]),
        ("%Y-%d-%m %H:%M:%S", [_dt.datetime(2024, 5, 1, 6, 7, 8), _dt.datetime(2024, 3, 2, 9, 10, 11), _dt.datetime(2024, 11, 3, 12, 13, 14)]),
    ],
)
def test_to_datetime_honors_format(
    backend_name, fmt, expected, backend_factory, collect_expr
) -> None:
    df = backend_factory.create(_DT_DATA, backend_name)
    got = collect_expr(df, ma.col("s").str.to_datetime(fmt))
    assert got == expected


_SLASH_DATA = {"s": ["15/03/2024", "20/06/2024", "01/12/2024"]}
_SLASH_DATES = [_dt.date(2024, 3, 15), _dt.date(2024, 6, 20), _dt.date(2024, 12, 1)]


@pytest.mark.parametrize("backend_name", TO_DATE_HONORING_BACKENDS)
def test_to_date_honors_slash_format(backend_name, backend_factory, collect_expr) -> None:
    df = backend_factory.create(_SLASH_DATA, backend_name)
    got = collect_expr(df, ma.col("s").str.to_date("%d/%m/%Y"))
    assert got == _SLASH_DATES


def test_to_date_is_gated_on_narwhals_pandas(backend_factory) -> None:
    df = backend_factory.create(_DATA, "narwhals-pandas")
    with pytest.raises(BackendCapabilityError, match="to_date"):
        ma.col("s").str.to_date("%Y-%m-%d").compile(df)


@pytest.mark.parametrize("op", ["to_date", "to_datetime"])
def test_strptime_is_gated_on_ibis_sqlite(op, backend_factory) -> None:
    df = backend_factory.create(_DATA, "ibis-sqlite")
    with pytest.raises(BackendCapabilityError):
        getattr(ma.col("s").str, op)("%Y-%m-%d").compile(df)
