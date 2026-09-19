"""Cross-backend behaviour for strptime `format` (spec 2026-07-28 section 3, PR-B)."""
from __future__ import annotations

import datetime as _dt

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)

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

# Default pandas storage cannot materialize Narwhals `to_date` as a typed date
# series. Arrow-backed pandas strings retain the supported native behavior.
# ibis-sqlite intrinsically refuses formatted date and timestamp parsing.
_DEFAULT_PANDAS_DATE_STORAGE = frozenset({"pandas", "narwhals-pandas"})
TO_DATE_HONORING_BACKENDS = [
    b for b in STRPTIME_BACKENDS
    if b not in {"ibis-sqlite", *_DEFAULT_PANDAS_DATE_STORAGE}
]
# ibis-sqlite is the only dialect declared UNSUPPORTED for str.to_datetime.
TO_DATETIME_HONORING_BACKENDS = [
    b for b in STRPTIME_BACKENDS if b != "ibis-sqlite"
]

# Ambiguous input: "2024-01-05" parses cleanly under BOTH formats and yields
# different dates, so the probe discriminates without relying on a parse error.
_DATA = {"s": ["2024-01-05", "2024-02-03", "2024-03-11", None]}
_DT_DATA = {
    "s": [
        "2024-01-05 06:07:08",
        "2024-02-03 09:10:11",
        "2024-03-11 12:13:14",
        None,
    ]
}

_ISO_DATES = [
    _dt.date(2024, 1, 5),
    _dt.date(2024, 2, 3),
    _dt.date(2024, 3, 11),
    None,
]
_SWAPPED_DATES = [
    _dt.date(2024, 5, 1),
    _dt.date(2024, 3, 2),
    _dt.date(2024, 11, 3),
    None,
]


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
        (
            "%Y-%m-%d %H:%M:%S",
            [
                _dt.datetime(2024, 1, 5, 6, 7, 8),
                _dt.datetime(2024, 2, 3, 9, 10, 11),
                _dt.datetime(2024, 3, 11, 12, 13, 14),
                None,
            ],
        ),
        (
            "%Y-%d-%m %H:%M:%S",
            [
                _dt.datetime(2024, 5, 1, 6, 7, 8),
                _dt.datetime(2024, 3, 2, 9, 10, 11),
                _dt.datetime(2024, 11, 3, 12, 13, 14),
                None,
            ],
        ),
    ],
)
def test_to_datetime_honors_format(
    backend_name, fmt, expected, backend_factory, collect_expr
) -> None:
    df = backend_factory.create(_DT_DATA, backend_name)
    got = collect_expr(df, ma.col("s").str.to_datetime(fmt))
    assert got == expected


_SLASH_DATA = {"s": ["15/03/2024", "20/06/2024", "01/12/2024", None]}
_SLASH_DATES = [
    _dt.date(2024, 3, 15),
    _dt.date(2024, 6, 20),
    _dt.date(2024, 12, 1),
    None,
]


@pytest.mark.parametrize("backend_name", TO_DATE_HONORING_BACKENDS)
def test_to_date_honors_slash_format(backend_name, backend_factory, collect_expr) -> None:
    df = backend_factory.create(_SLASH_DATA, backend_name)
    got = collect_expr(df, ma.col("s").str.to_date("%d/%m/%Y"))
    assert got == _SLASH_DATES




@pytest.mark.parametrize("backend_name", _DEFAULT_PANDAS_DATE_STORAGE)
def test_to_date_default_pandas_storage_is_a_native_boundary(
    backend_name, backend_factory, collect_expr
) -> None:
    df = backend_factory.create(_DATA, backend_name)

    with pytest.raises(NotImplementedError):
        collect_expr(df, ma.col("s").str.to_date("%Y-%m-%d"))


@pytest.mark.parametrize("backend_name", _DEFAULT_PANDAS_DATE_STORAGE)
def test_to_date_arrow_backed_pandas_strings_honor_format(
    backend_name, collect_expr
) -> None:
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa

    dataframe = pd.DataFrame(
        {"s": pd.Series(_DATA["s"], dtype=pd.ArrowDtype(pa.string()))}
    )
    if backend_name == "narwhals-pandas":
        dataframe = nw.from_native(dataframe, eager_only=True)

    assert collect_expr(dataframe, ma.col("s").str.to_date("%Y-%m-%d")) == _ISO_DATES


@pytest.mark.parametrize(
    ("op", "function_key"),
    [
        ("to_date", FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE),
        ("to_datetime", FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP),
    ],
)
def test_strptime_is_intrinsically_refused_on_ibis_sqlite(
    op, function_key, backend_factory
) -> None:
    df = backend_factory.create(_DATA, "ibis-sqlite")
    with pytest.raises(BackendCapabilityError) as raised:
        getattr(ma.col("s").str, op)("%Y-%m-%d").compile(df)
    assert raised.value.function_key is function_key
    assert raised.value.backend == "ibis"
    assert raised.value.limitation is None
