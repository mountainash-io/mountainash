"""Tests for temporal format parsing in conform pipeline.

Frictionless Table Schema specifies that date/datetime/time fields may carry
a ``format`` string with strptime patterns.  When format is "default" or None
the existing canonical default cast handles ISO parsing; when a custom pattern is
provided, the conform pipeline should use ``str.to_date``/``str.to_datetime``/
``str.to_time`` for explicit parsing.

Backend support (post strptime-format-honoring fix):
- to_date: honored on polars, polars-lazy, narwhals-polars, narwhals-lazy,
  ibis-duckdb, ibis-polars; gated (BackendCapabilityError) on ibis-sqlite,
  narwhals-pandas, pandas
- to_datetime: honored on all except ibis-sqlite; gated on ibis-sqlite
- to_time: polars / polars-lazy only (not yet wired for other backends)
"""
from __future__ import annotations

from datetime import date, datetime, time

import pytest
import polars as pl
import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS


_DATE_GATED = frozenset({"ibis-sqlite", "narwhals-pandas", "pandas"})
_DATETIME_GATED = frozenset({"ibis-sqlite"})
_TIME_HONORED = sorted({"polars", "polars-lazy"})


# ---------------------------------------------------------------------------
# Unit tests: _build_conform_exprs emits temporal format expressions
# ---------------------------------------------------------------------------


class TestBuildConformExprsTemporalFormat:
    """Unit tests that the expression builder emits temporal format logic."""

    def test_emits_expr_for_custom_date_format(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="%d/%m/%Y"),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_emits_expr_for_custom_datetime_format(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(
                    name="ts",
                    type=UniversalType.DATETIME,
                    format="%d/%m/%Y %H:%M:%S",
                ),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_emits_expr_for_custom_time_format(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="t", type=UniversalType.TIME, format="%H-%M-%S"),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_default_format_does_not_use_strptime(self):
        """Default format should fall through to canonical default cast."""
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="default"),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_none_format_does_not_use_strptime(self):
        """None format should fall through to canonical default cast."""
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format=None),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_any_format_does_not_use_strptime(self):
        """'any' format should fall through to canonical default cast (best-effort)."""
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="any"),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1


# ---------------------------------------------------------------------------
# Integration tests: custom date format parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDateFormatParsing:
    """Custom strptime format for date fields (honored broadly; gated on ibis-sqlite, narwhals-pandas, pandas)."""

    def test_strptime_date_dmy(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"dt": ["26/01/2024", "15/06/2023"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="%d/%m/%Y"),
            ],
        )
        if backend_name in _DATE_GATED:
            with pytest.raises(BackendCapabilityError):
                ma.relation(df).conform(spec).to_polars()
        else:
            result = ma.relation(df).conform(spec).to_polars()
            assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15)]

    def test_strptime_date_mdy(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"dt": ["01-26-2024", "06-15-2023"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="%m-%d-%Y"),
            ],
        )
        if backend_name in _DATE_GATED:
            with pytest.raises(BackendCapabilityError):
                ma.relation(df).conform(spec).to_polars()
        else:
            result = ma.relation(df).conform(spec).to_polars()
            assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15)]


# ---------------------------------------------------------------------------
# Integration tests: custom datetime format parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDatetimeFormatParsing:
    """Custom strptime format for datetime fields (honored on all except ibis-sqlite)."""

    def test_strptime_datetime_format(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"ts": ["26/01/2024 09:15:00"]}, backend_name
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
            with pytest.raises(BackendCapabilityError):
                ma.relation(df).conform(spec).to_polars()
        else:
            result = ma.relation(df).conform(spec).to_polars()
            vals = result["ts"].to_list()
            assert vals[0].year == 2024
            assert vals[0].month == 1
            assert vals[0].day == 26
            assert vals[0].hour == 9
            assert vals[0].minute == 15
            assert vals[0].second == 0


# ---------------------------------------------------------------------------
# Integration tests: custom time format parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", _TIME_HONORED)
class TestTimeFormatParsing:
    """Custom strptime format for time fields (Polars-only)."""

    def test_strptime_time_format(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"t": ["09-15-30", "14-30-00"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="t", type=UniversalType.TIME, format="%H-%M-%S"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["t"].to_list() == [time(9, 15, 30), time(14, 30, 0)]


# ---------------------------------------------------------------------------
# Integration tests: default/None format uses canonical default cast
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDefaultFormatFallback:
    """Default and None formats use canonical default cast (ISO parsing)."""

    def test_default_format_uses_cast(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"dt": ["2024-01-26", "2023-06-15"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="default"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15)]

    def test_none_format_uses_cast(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"dt": ["2024-01-26", "2023-06-15"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15)]

    def test_any_format_uses_cast(self, backend_name, backend_factory):
        """'any' format falls through to canonical default cast."""
        df = backend_factory.create(
            {"dt": ["2024-01-26", "2023-06-15"]}, backend_name
        )
        spec = TypeSpec(fields_match="open", 
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="any"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15)]
