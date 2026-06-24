"""Tests for temporal format parsing in conform pipeline.

Frictionless Table Schema specifies that date/datetime/time fields may carry
a ``format`` string with strptime patterns.  When format is "default" or None
the existing canonical default cast handles ISO parsing; when a custom pattern is
provided, the conform pipeline should use ``str.to_date``/``str.to_datetime``/
``str.to_time`` for explicit parsing.

Backend support:
- Polars: full support for str.to_date, str.to_datetime, str.to_time
- Narwhals: strptime not supported (raises NotImplementedError)
- Ibis: strptime not supported (falls back to cast)

Custom format tests are therefore Polars-only.  Default/None format tests run
on all backends since they use canonical default cast.
"""
from __future__ import annotations

from datetime import date, datetime, time

import pytest
import polars as pl
import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from fixtures.backend_registry import ALL_BACKENDS

# ALL_BACKENDS = [
#     "polars",
#     "pandas",
#     "narwhals",
#     "ibis-polars",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]

# Custom strptime format parsing only works on Polars (Narwhals/Ibis lack
# str.to_date/to_datetime/to_time support).
POLARS_ONLY = ["polars"]
_POLARS_BACKENDS = frozenset({"polars", "polars-lazy"})


def _xfail_polars_only_temporal(backend_name: str, also_ok: tuple[str, ...] = ()) -> None:
    """xfail custom temporal-format parsing on backends that lack it.

    Only Polars implements ``str.to_date``/``str.to_datetime``/``str.to_time``
    with an explicit strptime ``format``. narwhals raises
    ``NotImplementedError`` (strptime_date/strptime_timestamp) /
    ``BackendCapabilityError`` (str.to_time); ibis cannot parse non-ISO format
    strings. These are genuine upstream-library limits. ``also_ok`` lists
    non-Polars backends that incidentally succeed (e.g. ibis-polars executes on
    the Polars engine), so they keep running rather than XPASS-ing.
    """
    if backend_name in _POLARS_BACKENDS or backend_name in also_ok:
        return
    pytest.xfail(
        f"{backend_name}: custom temporal strptime format is Polars-only — "
        "narwhals lacks strptime_date/strptime_timestamp/str.to_time and ibis "
        "cannot parse non-ISO format strings"
    )


# ---------------------------------------------------------------------------
# Unit tests: _build_conform_exprs emits temporal format expressions
# ---------------------------------------------------------------------------


class TestBuildConformExprsTemporalFormat:
    """Unit tests that the expression builder emits temporal format logic."""

    def test_emits_expr_for_custom_date_format(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="%d/%m/%Y"),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_emits_expr_for_custom_datetime_format(self):
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
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

        spec = TypeSpec(
            fields=[
                FieldSpec(name="t", type=UniversalType.TIME, format="%H-%M-%S"),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_default_format_does_not_use_strptime(self):
        """Default format should fall through to canonical default cast."""
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="default"),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_none_format_does_not_use_strptime(self):
        """None format should fall through to canonical default cast."""
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format=None),
            ],
        )
        result = _build_conform_exprs(spec)
        assert len(result.exprs) == 1

    def test_any_format_does_not_use_strptime(self):
        """'any' format should fall through to canonical default cast (best-effort)."""
        from mountainash.conform.expressions import _build_conform_exprs

        spec = TypeSpec(
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
    """Custom strptime format for date fields (Polars-only)."""

    def test_strptime_date_dmy(self, backend_name, backend_factory):
        _xfail_polars_only_temporal(backend_name)
        df = backend_factory.create(
            {"dt": ["26/01/2024", "15/06/2023"]}, backend_name
        )
        spec = TypeSpec(
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="%d/%m/%Y"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15)]

    def test_strptime_date_mdy(self, backend_name, backend_factory):
        _xfail_polars_only_temporal(backend_name)
        df = backend_factory.create(
            {"dt": ["01-26-2024", "06-15-2023"]}, backend_name
        )
        spec = TypeSpec(
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="%m-%d-%Y"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15)]


# ---------------------------------------------------------------------------
# Integration tests: custom datetime format parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDatetimeFormatParsing:
    """Custom strptime format for datetime fields (Polars-only)."""

    def test_strptime_datetime_format(self, backend_name, backend_factory):
        # ibis-polars executes on the Polars engine, so it parses the custom
        # datetime format too — keep it running rather than xfail it.
        _xfail_polars_only_temporal(backend_name, also_ok=("ibis-polars",))
        df = backend_factory.create(
            {"ts": ["26/01/2024 09:15:00"]}, backend_name
        )
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="ts",
                    type=UniversalType.DATETIME,
                    format="%d/%m/%Y %H:%M:%S",
                ),
            ],
        )
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


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTimeFormatParsing:
    """Custom strptime format for time fields (Polars-only)."""

    def test_strptime_time_format(self, backend_name, backend_factory):
        _xfail_polars_only_temporal(backend_name)
        df = backend_factory.create(
            {"t": ["09-15-30", "14-30-00"]}, backend_name
        )
        spec = TypeSpec(
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
        spec = TypeSpec(
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
        spec = TypeSpec(
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
        spec = TypeSpec(
            fields=[
                FieldSpec(name="dt", type=UniversalType.DATE, format="any"),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["dt"].to_list() == [date(2024, 1, 26), date(2023, 6, 15)]
