"""Tests for temporal format parsing in conform pipeline.

Frictionless Table Schema specifies that date/datetime/time fields may carry
a ``format`` string with strptime patterns.  When format is "default" or None
the existing canonical default cast handles ISO parsing; when a custom pattern is
provided, the conform pipeline should use ``str.to_date``/``str.to_datetime``/
``str.to_time`` for explicit parsing.

Backend support:
- to_date: honored on polars, polars-lazy, narwhals-polars, narwhals-lazy,
  ibis-duckdb and ibis-polars; ibis-sqlite rejects the operation. Default
  pandas string storage cannot materialize Narwhals `to_date`, while Arrow-backed
  pandas strings preserve the supported native behavior.
- to_datetime: honored on all except ibis-sqlite; ibis-sqlite rejects it.
- to_time: polars / polars-lazy only (not yet wired for other backends)
"""
from __future__ import annotations

from datetime import date, datetime, time

import pytest

import mountainash as ma
from mountainash.conform.errors import ConformTransformError
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME,
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS


_DATE_REFUSED = frozenset({"ibis-sqlite"})
_DEFAULT_PANDAS_DATE_STORAGE = frozenset({"pandas", "narwhals-pandas"})
_DATETIME_GATED = frozenset({"ibis-sqlite"})
_TIME_HONORED = sorted({"polars", "polars-lazy"})
_TEMPORAL_ANY_SUPPORTED = frozenset({"polars", "polars-lazy"})




# ---------------------------------------------------------------------------
# Integration tests: custom date format parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize(
    ("values", "format"),
    [
        (["26/01/2024", "15/06/2023", None], "%d/%m/%Y"),
        (["01-26-2024", "06-15-2023", None], "%m-%d-%Y"),
    ],
)
def test_strptime_date_honors_format_or_reports_default_pandas_storage(
    backend_name, values, format, backend_factory
):
    df = backend_factory.create({"dt": values}, backend_name)
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="dt", type=UniversalType.DATE, format=format)],
    )
    if backend_name in _DATE_REFUSED:
        with pytest.raises(BackendCapabilityError) as raised:
            ma.relation(df).conform(spec).to_polars()
        assert raised.value.function_key is FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE
        assert raised.value.backend == "ibis"
        assert raised.value.limitation is None
    elif backend_name in _DEFAULT_PANDAS_DATE_STORAGE:
        with pytest.raises(ConformTransformError) as raised:
            ma.relation(df).conform(spec).to_polars()
        assert isinstance(raised.value.original_error, NotImplementedError)
    else:
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15), None]


@pytest.mark.parametrize("backend_name", ("pandas", "narwhals-pandas"))
@pytest.mark.parametrize(
    ("values", "format"),
    [
        (["26/01/2024", "15/06/2023", None], "%d/%m/%Y"),
        (["01-26-2024", "06-15-2023", None], "%m-%d-%Y"),
    ],
)
def test_strptime_date_honors_format_with_arrow_backed_pandas_strings(
    backend_name, values, format
):
    import narwhals as nw
    import pandas as pd
    import pyarrow as pa

    dataframe = pd.DataFrame(
        {
            "dt": pd.Series(values, dtype=pd.ArrowDtype(pa.string())),
            "unmapped": ["retained", None, "unchanged"],
        }
    )
    if backend_name == "narwhals-pandas":
        dataframe = nw.from_native(dataframe, eager_only=True)
    spec = TypeSpec(
        fields_match="open",
        fields=[FieldSpec(name="dt", type=UniversalType.DATE, format=format)],
    )
    result = ma.relation(dataframe).conform(spec).to_polars()
    assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15), None]
    assert result["unmapped"].to_list() == ["retained", None, "unchanged"]


# ---------------------------------------------------------------------------
# Integration tests: custom datetime format parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDatetimeFormatParsing:
    """Custom strptime format for datetime fields (honored on all except ibis-sqlite)."""

    def test_strptime_datetime_format(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"ts": ["26/01/2024 09:15:00", None]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="ts",
                    type=UniversalType.DATETIME,
                    format="%d/%m/%Y %H:%M:%S",
                ),
            ],
        )
        if backend_name in _DATETIME_GATED:
            with pytest.raises(BackendCapabilityError) as raised:
                ma.relation(df).conform(spec).to_polars()
            assert (
                raised.value.function_key
                is FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP
            )
            assert raised.value.backend == "ibis"
            assert raised.value.limitation is None
        else:
            result = ma.relation(df).conform(spec).to_polars()
            assert result["ts"].to_list() == [datetime(2024, 1, 26, 9, 15), None]


# ---------------------------------------------------------------------------
# Integration tests: custom time format parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", _TIME_HONORED)
class TestTimeFormatParsing:
    """Custom strptime format for time fields (Polars-only)."""

    def test_strptime_time_format(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"t": ["09-15-30", "14-30-00", None]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="t", type=UniversalType.TIME, format="%H-%M-%S"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["t"].to_list() == [time(9, 15, 30), time(14, 30), None]


# ---------------------------------------------------------------------------
# Integration tests: default/None format uses canonical default cast
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDefaultFormatFallback:
    """Default and None formats use canonical default cast (ISO parsing)."""

    def test_default_format_uses_cast(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"dt": ["2024-01-26", "2023-06-15", None]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="default"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15), None]

    def test_none_format_uses_cast(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"dt": ["2024-01-26", "2023-06-15", None]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15), None]
    def test_any_format_uses_temporal_parser_or_gate(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"dt": ["2024-01-26", "2023-06-15", None]}, backend_name
        )
        spec = TypeSpec(
            fields_match="open",
            fields=[FieldSpec(name="dt", type=UniversalType.DATE, format="any")],
        )
        if backend_name not in _TEMPORAL_ANY_SUPPORTED:
            with pytest.raises(BackendCapabilityError) as raised:
                ma.relation(df).conform(spec).to_polars()
            assert (
                raised.value.function_key
                is FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_TEMPORAL_ANY
            )
            assert raised.value.backend == (
                "ibis" if backend_name.startswith("ibis") else "narwhals"
            )
            assert raised.value.limitation is None
            return
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15), None]
