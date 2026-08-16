"""Argument channel tests for datetime operations.

The add_* operations (add_days, add_hours, etc.) have KNOWN_EXPR_LIMITATIONS
on narwhals (literal-only offset) and ibis (ibis.interval rejects expressions).
On ibis, the TypeError fires at execution time (not compile time), so the test
template fallback catch in _test_template.py:137-145 handles error enrichment.

The diff_* operations (diff_days, diff_hours, etc.) take a second datetime
expression as `other`.  The complex_builder offsets the `other` column by 1 day
to exercise a genuine sub-expression rather than a bare column reference.

Skipped params (not added as OP_SPECS):
- diff_milliseconds.other: API builder has no diff_milliseconds method (returns None).
- assume_timezone.timezone, to_timezone.timezone, local_timestamp.timezone, strftime.format,
  truncate.unit, ceil.unit, floor.unit, round.unit: these are passed as options
  (not visited expressions) in the API builder; lit/col/complex input types fail with TypeError.
  ceil/floor/round are additionally broken even with raw args (name collision with numeric rounding).
- extract.component, extract.timezone, extract_boolean.component: internal dispatch
  params used by the visitor, not exposed via the fluent API.
- round_temporal.*, round_calendar.*: options (int/str literals), not expression args.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import mountainash as ma
from mountainash.core.errors import InvalidOptionValueError
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.datetime_components import (
    BooleanComponent,
    DatetimeComponent,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME as FK_DT,
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_MA_DT,
)
from expressions.argument_types.conftest import ALL_BACKENDS, make_df
from expressions.argument_types._option_helpers import (
    OptionProbeDidNotDiscriminateError,
    OptionSpec,
    option_result,
    xfail_option_unsupported,
)
from expressions.argument_types.option_disposition import (
    INVALID_OPTION_VALUE,
    OPTION_DISPOSITIONS,
    OPTION_FAMILY_DEFAULT_FACT_KEYS,
    REGISTERED_INVALID_OPTION_REJECTIONS,
    REGISTERED_OPTION_PROBES,
    InvalidOptionRejection,
    OptionCell,
    OptionProbeRegistration,
    param_taxonomy,
)
from mountainash.core.constants import CONST_BACKEND
from expressions.argument_types._test_template import (
    INPUT_TYPES,
    OpSpec,
    run_argument_matrix,
    xfail_if_limited,
)

TESTED_PARAMS: list[tuple] = [
    ("add", "x"),
    ("add", "y"),
    (FK_MA_DT.ADD_DAYS, "days"),
    (FK_MA_DT.ADD_DAYS, "x"),
    (FK_MA_DT.ADD_HOURS, "hours"),
    (FK_MA_DT.ADD_HOURS, "x"),
    ("add_intervals", "x"),
    ("add_intervals", "y"),
    (FK_MA_DT.ADD_MICROSECONDS, "microseconds"),
    (FK_MA_DT.ADD_MICROSECONDS, "x"),
    (FK_MA_DT.ADD_MILLISECONDS, "milliseconds"),
    (FK_MA_DT.ADD_MILLISECONDS, "x"),
    (FK_MA_DT.ADD_MINUTES, "minutes"),
    (FK_MA_DT.ADD_MINUTES, "x"),
    (FK_MA_DT.ADD_MONTHS, "months"),
    (FK_MA_DT.ADD_MONTHS, "x"),
    (FK_MA_DT.ADD_SECONDS, "seconds"),
    (FK_MA_DT.ADD_SECONDS, "x"),
    (FK_MA_DT.ADD_YEARS, "x"),
    (FK_MA_DT.ADD_YEARS, "years"),
    # assume_timezone.timezone, to_timezone.timezone, local_timestamp.timezone, ceil.unit,
    # floor.unit, round.unit, truncate.unit, strftime.format: reclassified as option
    # (concrete str) — tested in TESTED_OPTION_PARAMS.
    (FK_DT.ASSUME_TIMEZONE, "x"),
    (FK_MA_DT.CEIL, "x"),
    ("day", "x"),
    ("day_of_week", "x"),
    ("day_of_year", "x"),
    (FK_MA_DT.DIFF_DAYS, "other"),
    (FK_MA_DT.DIFF_DAYS, "x"),
    (FK_MA_DT.DIFF_HOURS, "other"),
    (FK_MA_DT.DIFF_HOURS, "x"),
    (FK_MA_DT.DIFF_MILLISECONDS, "other"),
    (FK_MA_DT.DIFF_MILLISECONDS, "x"),
    (FK_MA_DT.DIFF_MINUTES, "other"),
    (FK_MA_DT.DIFF_MINUTES, "x"),
    (FK_MA_DT.DIFF_MONTHS, "other"),
    (FK_MA_DT.DIFF_MONTHS, "x"),
    (FK_MA_DT.DIFF_SECONDS, "other"),
    (FK_MA_DT.DIFF_SECONDS, "x"),
    (FK_MA_DT.DIFF_YEARS, "other"),
    (FK_MA_DT.DIFF_YEARS, "x"),
    # extract.component, extract.timezone, extract_boolean.component: reclassified as option
    (FK_DT.EXTRACT, "x"),
    (FK_DT.EXTRACT_BOOLEAN, "x"),
    (FK_MA_DT.FLOOR, "x"),
    ("gt", "x"),
    ("gt", "y"),
    ("gte", "x"),
    ("gte", "y"),
    ("hour", "x"),
    (FK_MA_DT.IS_DST, "x"),
    (FK_MA_DT.IS_LEAP_YEAR, "x"),
    ("iso_year", "x"),
    (FK_DT.LOCAL_TIMESTAMP, "x"),
    ("lt", "x"),
    ("lt", "y"),
    ("lte", "x"),
    ("lte", "y"),
    ("microsecond", "x"),
    ("millisecond", "x"),
    ("minute", "x"),
    ("month", "x"),
    ("multiply", "x"),
    ("multiply", "y"),
    ("nanosecond", "x"),
    (FK_MA_DT.OFFSET_BY, "x"),
    ("quarter", "x"),
    (FK_MA_DT.ROUND, "x"),
    # round_calendar/round_temporal option params: multiple, origin, rounding, unit all
    # reclassified as option in protocol commit 5fd72c5 — removed from TESTED_PARAMS.
    ("round_calendar", "x"),
    ("round_temporal", "x"),
    ("second", "x"),
    (FK_DT.STRFTIME, "x"),
    ("strptime_date", "x"),
    ("strptime_time", "x"),
    ("strptime_timestamp", "x"),
    ("subtract", "x"),
    ("subtract", "y"),
    ("timezone_offset", "x"),
    (FK_MA_DT.TO_TIMEZONE, "x"),
    (FK_MA_DT.TRUNCATE, "x"),
    ("unix_timestamp", "x"),
    ("week_of_year", "x"),
    ("year", "x"),
    (FK_MA_DT.TOTAL_SECONDS, "x"),
    (FK_MA_DT.TOTAL_MINUTES, "x"),
    (FK_MA_DT.TOTAL_MILLISECONDS, "x"),
    (FK_MA_DT.TOTAL_MICROSECONDS, "x"),
]

_TZ_MATRIX_DATA = {
    "ts": [
        datetime(2026, 7, 21, 13, 37, 45, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
    ],
}

OP_SPECS: list[OpSpec] = [
    OpSpec(
        function_key=FK_MA_DT.ADD_DAYS,
        op_name="add_days",
        build=lambda col, arg: col.dt.add_days(arg),
        raw_arg=5,
        arg_col_name="days",
        param_name="days",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "days": [5, 10, 3],
        },
        input_col="dt",
    ),
    OpSpec(
        function_key=FK_MA_DT.ADD_HOURS,
        op_name="add_hours",
        build=lambda col, arg: col.dt.add_hours(arg),
        raw_arg=12,
        arg_col_name="hours",
        param_name="hours",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "hours": [12, 6, 24],
        },
        input_col="dt",
    ),
    OpSpec(
        function_key=FK_MA_DT.ADD_MINUTES,
        op_name="add_minutes",
        build=lambda col, arg: col.dt.add_minutes(arg),
        raw_arg=30,
        arg_col_name="minutes",
        param_name="minutes",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "minutes": [30, 45, 15],
        },
        input_col="dt",
    ),
    OpSpec(
        function_key=FK_MA_DT.ADD_SECONDS,
        op_name="add_seconds",
        build=lambda col, arg: col.dt.add_seconds(arg),
        raw_arg=90,
        arg_col_name="seconds",
        param_name="seconds",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "seconds": [90, 120, 60],
        },
        input_col="dt",
    ),
    OpSpec(
        function_key=FK_MA_DT.ADD_MILLISECONDS,
        op_name="add_milliseconds",
        build=lambda col, arg: col.dt.add_milliseconds(arg),
        raw_arg=500,
        arg_col_name="milliseconds",
        param_name="milliseconds",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "milliseconds": [500, 250, 1000],
        },
        input_col="dt",
    ),
    OpSpec(
        function_key=FK_MA_DT.ADD_MICROSECONDS,
        op_name="add_microseconds",
        build=lambda col, arg: col.dt.add_microseconds(arg),
        raw_arg=1000,
        arg_col_name="microseconds",
        param_name="microseconds",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "microseconds": [1000, 500, 2000],
        },
        input_col="dt",
    ),
    OpSpec(
        function_key=FK_MA_DT.ADD_MONTHS,
        op_name="add_months",
        build=lambda col, arg: col.dt.add_months(arg),
        raw_arg=3,
        arg_col_name="months",
        param_name="months",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "months": [3, 1, 6],
        },
        input_col="dt",
    ),
    OpSpec(
        function_key=FK_MA_DT.ADD_YEARS,
        op_name="add_years",
        build=lambda col, arg: col.dt.add_years(arg),
        raw_arg=1,
        arg_col_name="years",
        param_name="years",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "years": [1, 2, 5],
        },
        input_col="dt",
    ),
    # ------------------------------------------------------------------
    # Diff ops — `other` is a datetime expression argument
    # complex_builder offsets the `other` column by 1 day so the complex
    # input type exercises a genuine sub-expression, not just a column ref.
    # ------------------------------------------------------------------
    OpSpec(
        function_key=FK_MA_DT.DIFF_DAYS,
        op_name="diff_days",
        build=lambda col, arg: col.dt.diff_days(arg),
        raw_arg=datetime(2024, 1, 15),
        arg_col_name="other",
        param_name="other",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "other": [datetime(2023, 12, 31), datetime(2024, 1, 1), datetime(2024, 6, 1)],
        },
        input_col="dt",
        complex_builder=lambda cn: ma.col(cn).dt.add_days(1),
    ),
    OpSpec(
        function_key=FK_MA_DT.DIFF_HOURS,
        op_name="diff_hours",
        build=lambda col, arg: col.dt.diff_hours(arg),
        raw_arg=datetime(2024, 1, 15),
        arg_col_name="other",
        param_name="other",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "other": [datetime(2023, 12, 31), datetime(2024, 1, 1), datetime(2024, 6, 1)],
        },
        input_col="dt",
        complex_builder=lambda cn: ma.col(cn).dt.add_days(1),
    ),
    OpSpec(
        function_key=FK_MA_DT.DIFF_MINUTES,
        op_name="diff_minutes",
        build=lambda col, arg: col.dt.diff_minutes(arg),
        raw_arg=datetime(2024, 1, 15),
        arg_col_name="other",
        param_name="other",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "other": [datetime(2023, 12, 31), datetime(2024, 1, 1), datetime(2024, 6, 1)],
        },
        input_col="dt",
        complex_builder=lambda cn: ma.col(cn).dt.add_days(1),
    ),
    OpSpec(
        function_key=FK_MA_DT.DIFF_SECONDS,
        op_name="diff_seconds",
        build=lambda col, arg: col.dt.diff_seconds(arg),
        raw_arg=datetime(2024, 1, 15),
        arg_col_name="other",
        param_name="other",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "other": [datetime(2023, 12, 31), datetime(2024, 1, 1), datetime(2024, 6, 1)],
        },
        input_col="dt",
        complex_builder=lambda cn: ma.col(cn).dt.add_days(1),
    ),
    OpSpec(
        function_key=FK_MA_DT.DIFF_MONTHS,
        op_name="diff_months",
        build=lambda col, arg: col.dt.diff_months(arg),
        raw_arg=datetime(2024, 1, 15),
        arg_col_name="other",
        param_name="other",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "other": [datetime(2023, 12, 31), datetime(2024, 1, 1), datetime(2024, 6, 1)],
        },
        input_col="dt",
        complex_builder=lambda cn: ma.col(cn).dt.add_days(1),
    ),
    OpSpec(
        function_key=FK_MA_DT.DIFF_YEARS,
        op_name="diff_years",
        build=lambda col, arg: col.dt.diff_years(arg),
        raw_arg=datetime(2024, 1, 15),
        arg_col_name="other",
        param_name="other",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "other": [datetime(2023, 12, 31), datetime(2024, 1, 1), datetime(2024, 6, 1)],
        },
        input_col="dt",
        complex_builder=lambda cn: ma.col(cn).dt.add_days(1),
    ),
    OpSpec(
        function_key=FK_MA_DT.DIFF_MILLISECONDS,
        op_name="diff_milliseconds",
        build=lambda col, arg: col.dt.diff_milliseconds(arg),
        raw_arg=datetime(2024, 1, 15),
        arg_col_name="other",
        param_name="other",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "other": [datetime(2023, 12, 31), datetime(2024, 1, 1), datetime(2024, 6, 1)],
        },
        input_col="dt",
        complex_builder=lambda cn: ma.col(cn).dt.add_days(1),
    ),
    OpSpec(
        function_key="add_intervals",
        op_name="add_intervals",
        build=lambda col, arg: col.dt.add_intervals(arg),
        raw_arg=timedelta(days=5),
        arg_col_name="interval",
        param_name="y",
        input_col="dt",
        data={
            "dt": [datetime(2024, 1, 1), datetime(2024, 6, 15), datetime(2024, 12, 31)],
            "interval": [timedelta(days=5), timedelta(hours=12), timedelta(days=1)],
        },
        complex_builder=lambda cn: ma.col(cn),
    ),
    # to_timezone.x / local_timestamp.x: item 71 — the receiver itself (not an
    # ignored placeholder) varies raw/lit/col/complex; timezone is a FIXED
    # emitted option (Australia/Sydney), so first_scalar_build_gate() sees the
    # real IANA_TIMEZONE class fact regardless of input_type. build() returns
    # the to_timezone/local_timestamp call directly (not wrapped in .dt.hour())
    # so cell.node IS the gated ScalarFunctionNode, not an outer composition —
    # first_scalar_build_gate() only inspects the top-level node's own
    # arguments/options, matching production's per-node visitor dispatch.
    OpSpec(
        function_key=FK_MA_DT.TO_TIMEZONE,
        op_name="to_timezone",
        build=lambda receiver, _arg: receiver.dt.to_timezone("Australia/Sydney"),
        raw_arg=datetime(2026, 7, 21, 13, 37, 45, tzinfo=timezone.utc),
        arg_col_name="ts",
        param_name="x",
        data=_TZ_MATRIX_DATA,
        matrix_arg_is_input=True,
        complex_builder=lambda cn: ma.col(cn).dt.offset_by("1d"),
    ),
    OpSpec(
        function_key=FK_DT.LOCAL_TIMESTAMP,
        op_name="local_timestamp",
        build=lambda receiver, _arg: receiver.dt.local_timestamp("Australia/Sydney"),
        raw_arg=datetime(2026, 7, 21, 13, 37, 45, tzinfo=timezone.utc),
        arg_col_name="ts",
        param_name="x",
        data=_TZ_MATRIX_DATA,
        matrix_arg_is_input=True,
        complex_builder=lambda cn: ma.col(cn).dt.offset_by("1d"),
    ),
]


_DIFF_NW_XFAIL = pytest.mark.xfail(
    strict=False,
    raises=AttributeError,
    reason="Narwhals ExprDateTimeNamespace lacks total_days/total_hours/etc methods",
)

_NW_BACKENDS = {}#"narwhals-polars", "narwhals-pandas"}


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ALL_BACKENDS:
            for it in INPUT_TYPES:
                marks = []
                mark = xfail_if_limited(bk, op, it)
                if mark:
                    marks.append(mark)
                cases.append(
                    pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}")
                )
    return cases


if OP_SPECS:

    @pytest.mark.parametrize("op,backend,input_type", _params())
    def test_argument_channel(op: OpSpec, backend: str, input_type: str):
        run_argument_matrix(op, backend, input_type)


# ============================================================================
# Datetime `unit` option disposition (PR-C Task 3b)
# ----------------------------------------------------------------------------
# Verified matrix (controller Step-0 probe of all four fixtures, post-Task-3a):
#
#   | op          | polars | ibis (ibis-duckdb)         | narwhals (each dialect)    |
#   |-------------|--------|----------------------------|----------------------------|
#   | truncate    | ALL    | honor core+1w; declare 1q  | honor core+1q; declare 1w  |
#   | floor_dt    | ALL    | honor core+1w; declare 1q  | honor core+1q; declare 1w  |
#   | round_dt    | ALL    | declare EVERY value        | declare EVERY value        |
#   | ceil_dt     | ALL    | declare EVERY value        | declare EVERY value        |
#
# Portable core = {1y, 1mo, 1d, 1h, 1m, 1s, 1ms, 1us}. 1ns was dropped in
# Task 3a; the validator rejects it before the visitor. The visitor (with
# enforce_capabilities=True) raises BackendCapabilityError from the value-scoped
# UNSUPPORTED facts declared in capabilities/datetime/options.py. Backend
# round/ceil/floor impls are NOT edited — the capability facts are the only
# honesty mechanism. Per the brief, family / dialect separation mirrors the
# string `padding` slice: ibis declared values get BOTH a family-default
# (dialect=None) fact AND a dialect="ibis-duckdb" fact; narwhals declared
# values get per-dialect facts only (NEVER a single dialect=None narwhals
# family fact).
# ============================================================================

_DATETIME_PROTOCOL = "MountainAshScalarDatetimeExpressionSystemProtocol"
_DT = datetime(2026, 7, 21, 13, 37, 45)
_DATETIME_UNIT_DATA = {"ts": [_DT]}

# Per-build-value reference unit. The unit option has no default (the
# protocol marks ``unit: str`` as required), so the reference cannot be a
# no-op omission — it must be a DIFFERENT always-honored value than the
# build's. The test input (2026-07-21 13:37:45) is microsecond-aligned, so
# 1s, 1ms, 1us all give the same result; the reference for those fine units
# must use a coarser unit (1m, 1d, 1h, …) to actually differ. Each pair
# is hand-picked so build and reference always produce different results
# on every backend — critical for the ``expected_discriminates=True`` check
# on HONORED cells.
_REFERENCE_VALUE_BY_BUILD = {
    "1y": "1mo",
    "1mo": "1d",
    "1q": "1y",
    "1d": "1h",
    "1h": "1d",
    "1m": "1h",
    "1s": "1m",
    "1ms": "1m",
    "1us": "1m",
    "1w": "1d",
    # Friendly aliases — same value semantics as their canonical duration
    # form; the api builder normalizes them before validation. The
    # disposition inherits the same honored/declared matrix as the
    # canonical form (e.g. "year" is honored everywhere, "quarter" is
    # declared on ibis, "week" is declared on narwhals).
    "2d": "1h",
    "3h": "1h",
    # Friendly aliases — same value semantics as their canonical duration
    # form; the api builder normalizes them before validation. The
    # disposition inherits the same honored/declared matrix as the
    # canonical form (e.g. "year" is honored everywhere, "quarter" is
    # declared on ibis, "week" is declared on narwhals).
    "year": "1mo",
    "quarter": "1y",
    "month": "1d",
    "week": "1d",
    "day": "1h",
    "hour": "1d",
    "minute": "1h",
    "second": "1m",
    "millisecond": "1m",
    "microsecond": "1m",
}

_UNIT_OP_FKEYS = {
    "truncate": FK_MA_DT.TRUNCATE,
    "round_dt": FK_MA_DT.ROUND,
    "ceil_dt": FK_MA_DT.CEIL,
    "floor_dt": FK_MA_DT.FLOOR,
}
# The public api-builder method names — `truncate` and `floor` differ from
# the registry names; `round` and `ceil` map to round_dt/ceil_dt via the
# _*_dt MRO rename (Task 1). Mirroring the *api* names (not the FKEY names)
# in OPTION_DISPOSITIONS keeps the per-fixture disposition cell aligned with
# what the user types — OptionCell.op is canonical to the FKEY's
# protocol_method.__name__ (round_dt/ceil_dt/floor_dt/truncate).
_UNIT_API_METHODS = {
    "truncate": "truncate",
    "round_dt": "round",
    "ceil_dt": "ceil",
    "floor_dt": "floor",
}
# All MA domain values: duration forms + friendly aliases + multipliers.
_ALL_UNIT_VALUES = (
    "1y", "1mo", "1d", "1h", "1m", "1s", "1ms", "1us", "1w", "1q",
    "year", "quarter", "month", "week", "day", "hour", "minute",
    "second", "millisecond", "microsecond",
    "2d", "3h",
)


def _unit_expr(op: str, value: str):
    """Build a unit-rounding expression with an explicit value."""
    return getattr(ma.col("ts").dt, _UNIT_API_METHODS[op])(value)


def _unit_reference_expr(op: str, build_value: str):
    """Reference expression — always a DIFFERENT always-honored value."""
    return _unit_expr(op, _REFERENCE_VALUE_BY_BUILD[build_value])


# (op, value) pairs HELD OUT of the ibis-duckdb honor set; declared on ibis.
# Friendly aliases inherit the same disposition as their canonical duration
# form ("quarter" -> "1q", "week" -> "1w"), per the api-builder's friendly
# normalization at validate_ma_option.
_IBIS_DUCKDB_DECLARED_DURATION = {
    "truncate": {"1q", "2d", "3h"},
    "floor_dt": {"1q", "2d", "3h"},
    "round_dt": {"1y", "1mo", "1d", "1h", "1m", "1s", "1ms", "1us", "1w", "1q", "2d", "3h"},
    "ceil_dt": {"1y", "1mo", "1d", "1h", "1m", "1s", "1ms", "1us", "1w", "1q", "2d", "3h"},
}
_NARWHALS_DECLARED_DURATION = {
    "truncate": {"1w"},
    "floor_dt": {"1w"},
    "round_dt": {"1y", "1mo", "1d", "1h", "1m", "1s", "1ms", "1us", "1w", "1q", "2d", "3h"},
    "ceil_dt": {"1y", "1mo", "1d", "1h", "1m", "1s", "1ms", "1us", "1w", "1q", "2d", "3h"},
}
_FRIENDLY_TO_DURATION = {
    "year": "1y", "quarter": "1q", "month": "1mo", "week": "1w",
    "day": "1d", "hour": "1h", "minute": "1m", "second": "1s",
    "millisecond": "1ms", "microsecond": "1us",
}
_IBIS_DUCKDB_DECLARED = {
    op: declared | {friendly for friendly, dur in _FRIENDLY_TO_DURATION.items() if dur in declared}
    for op, declared in _IBIS_DUCKDB_DECLARED_DURATION.items()
}
_NARWHALS_DECLARED = {
    op: declared | {friendly for friendly, dur in _FRIENDLY_TO_DURATION.items() if dur in declared}
    for op, declared in _NARWHALS_DECLARED_DURATION.items()
}


def _unit_disposition(op: str, value: str, backend: str) -> str:
    """Mirror the verified matrix: honored or declared_unsupported per cell."""
    if backend == "polars":
        return "honored"  # polars honors ALL values; the matrix column
    if backend == "ibis":
        return "declared_unsupported" if value in _IBIS_DUCKDB_DECLARED[op] else "honored"
    # narwhals-polars and narwhals-pandas share the same per-dialect fact sets.
    return "declared_unsupported" if value in _NARWHALS_DECLARED[op] else "honored"


def _unit_backing_mode(op: str, value: str, backend: str) -> str:
    disp = _unit_disposition(op, value, backend)
    if disp != "declared_unsupported":
        return "absence"
    if value in {"2d", "3h"}:
        return "class"
    return "exact-fallback"


def _unit_reason(op: str, value: str, backend: str) -> str:
    if _unit_disposition(op, value, backend) == "honored":
        return "native backend honors the unit on this op"
    if backend == "ibis":
        if value in {"2d", "3h"}:
            return "ibis TimestampTruncate rejects Polars-style multiplier duration units (e.g. '2d', '3h', '12mo'); only single bare units are accepted"
        if op in {"round_dt", "ceil_dt"}:
            return "ibis has no native datetime round/ceil; silently falling back to truncate would return a wrong value"
        return "ibis TimestampTruncate rejects the quarter unit '1q' (and its friendly alias 'quarter')"
    # narwhals
    if value in {"2d", "3h"}:
        return "narwhals has no native datetime round/ceil; a multiplier value silently falls back to truncate and returns a wrong (down-rounded) result"
    if op in {"round_dt", "ceil_dt"}:
        return "narwhals has no native datetime round/ceil; silently falling back to truncate would return a wrong value"
    return "narwhals truncate rejects the week unit '1w' (and its friendly alias 'week')"


def _unit_probe(op: str, value: str, backend: str) -> OptionSpec:
    disposition = _unit_disposition(op, value, backend)
    if disposition == "honored":
        return OptionSpec(
            _UNIT_OP_FKEYS[op],
            "unit",
            value,
            "datetime",
            lambda v=value: _unit_expr(op, v),
            lambda v=value: _unit_reference_expr(op, v),
            _DATETIME_UNIT_DATA,
            expected_discriminates=True,
        )
    # declared_unsupported
    if backend == "ibis":
        return OptionSpec(
            _UNIT_OP_FKEYS[op],
            "unit",
            value,
            "datetime",
            lambda v=value: _unit_expr(op, v),
            lambda v=value: _unit_reference_expr(op, v),
            _DATETIME_UNIT_DATA,
            expected_discriminates=True,
        )
    # narwhals
    canonical = _FRIENDLY_TO_DURATION.get(value, value)
    if canonical == "1w":
        return OptionSpec(
            _UNIT_OP_FKEYS[op],
            "unit",
            value,
            "datetime",
            lambda v=value: _unit_expr(op, v),
            lambda v=value: _unit_reference_expr(op, v),
            _DATETIME_UNIT_DATA,
            expected_discriminates=True,
        )
    return OptionSpec(
        _UNIT_OP_FKEYS[op],
        "unit",
        value,
        "datetime",
        lambda v=value: _unit_expr(op, v),
        lambda v=value: _unit_expr(op, v),  # same value → always equal
        _DATETIME_UNIT_DATA,
        expected_discriminates=True,  # mismatch: probe raises sentinel
    )


def _unit_native_failure(op: str, value: str, backend: str):
    if backend == "ibis":
        from ibis.common.annotations import SignatureValidationError
        return SignatureValidationError
    # narwhals
    canonical = _FRIENDLY_TO_DURATION.get(value, value)
    if canonical == "1w":
        return ValueError
    return OptionProbeDidNotDiscriminateError


# Per-op, per-unit HONORED result (verified by the controller Step-0 probe).
_HONORED_RESULTS: dict[str, dict[str, datetime]] = {
    "truncate": {
        "1y": datetime(2026, 1, 1, 0, 0),
        "1mo": datetime(2026, 7, 1, 0, 0),
        "1d": datetime(2026, 7, 21, 0, 0),
        "1h": datetime(2026, 7, 21, 13, 0),
        "1m": datetime(2026, 7, 21, 13, 37),
        "1s": datetime(2026, 7, 21, 13, 37, 45),
        "1ms": datetime(2026, 7, 21, 13, 37, 45),
        "1us": datetime(2026, 7, 21, 13, 37, 45),
        "1w": datetime(2026, 7, 20, 0, 0),
        "1q": datetime(2026, 7, 1, 0, 0),
        "2d": datetime(2026, 7, 20, 0, 0),
        "3h": datetime(2026, 7, 21, 12, 0),
    },
    "round_dt": {
        "1y": datetime(2027, 1, 1, 0, 0),
        "1mo": datetime(2026, 8, 1, 0, 0),
        "1d": datetime(2026, 7, 22, 0, 0),
        "1h": datetime(2026, 7, 21, 14, 0),
        "1m": datetime(2026, 7, 21, 13, 38),
        "1s": datetime(2026, 7, 21, 13, 37, 45),
        "1ms": datetime(2026, 7, 21, 13, 37, 45),
        "1us": datetime(2026, 7, 21, 13, 37, 45),
        "1w": datetime(2026, 7, 20, 0, 0),
        "1q": datetime(2026, 7, 1, 0, 0),
        "2d": datetime(2026, 7, 22, 0, 0),
        "3h": datetime(2026, 7, 21, 15, 0),
    },
    "ceil_dt": {
        "1y": datetime(2027, 1, 1, 0, 0),
        "1mo": datetime(2026, 8, 1, 0, 0),
        "1d": datetime(2026, 7, 22, 0, 0),
        "1h": datetime(2026, 7, 21, 14, 0),
        "1m": datetime(2026, 7, 21, 13, 38),
        "1s": datetime(2026, 7, 21, 13, 37, 45),
        "1ms": datetime(2026, 7, 21, 13, 37, 45),
        "1us": datetime(2026, 7, 21, 13, 37, 45),
        "1w": datetime(2026, 7, 27, 0, 0),
        "1q": datetime(2026, 10, 1, 0, 0),
        "2d": datetime(2026, 7, 22, 0, 0),
        "3h": datetime(2026, 7, 21, 15, 0),
    },
    "floor_dt": {
        "1y": datetime(2026, 1, 1, 0, 0),
        "1mo": datetime(2026, 7, 1, 0, 0),
        "1d": datetime(2026, 7, 21, 0, 0),
        "1h": datetime(2026, 7, 21, 13, 0),
        "1m": datetime(2026, 7, 21, 13, 37),
        "1s": datetime(2026, 7, 21, 13, 37, 45),
        "1ms": datetime(2026, 7, 21, 13, 37, 45),
        "1us": datetime(2026, 7, 21, 13, 37, 45),
        "1w": datetime(2026, 7, 20, 0, 0),
        "1q": datetime(2026, 7, 1, 0, 0),
        "2d": datetime(2026, 7, 20, 0, 0),
        "3h": datetime(2026, 7, 21, 12, 0),
    },
}


@pytest.mark.parametrize("op", sorted(_UNIT_OP_FKEYS))
@pytest.mark.parametrize("value", _ALL_UNIT_VALUES)
@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_datetime_unit_option_honored_or_declared(
    op: str, value: str, backend: str, request
) -> None:
    fkey = _UNIT_OP_FKEYS[op]
    request.applymarker(
        xfail_option_unsupported(fkey, "unit", value, backend)
    )
    df = make_df(_DATETIME_UNIT_DATA, backend)
    canonical = _FRIENDLY_TO_DURATION.get(value, value)
    expected = _HONORED_RESULTS[op][canonical]
    got = option_result(df, _unit_expr(op, value), backend)
    assert got == [expected], (
        f"[{backend}] {op}('{value}') on {_DT!r} expected {[expected]!r}, got {got!r}"
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        _UNIT_OP_FKEYS[op],
        _DATETIME_PROTOCOL,
        op,
        "unit",
        backend,
        value,
        "datetime",
        _unit_disposition(op, value, backend),
        _unit_reason(op, value, backend),
        _unit_backing_mode(op, value, backend),
    )
    for op in sorted(_UNIT_OP_FKEYS)
    for backend in ALL_BACKENDS
    for value in _ALL_UNIT_VALUES
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _unit_probe(op, value, backend),
        backend,
        _unit_disposition(op, value, backend),
        _unit_native_failure(op, value, backend)
        if _unit_disposition(op, value, backend) == "declared_unsupported"
        else None,
    )
    for op in sorted(_UNIT_OP_FKEYS)
    for backend in ALL_BACKENDS
    for value in _ALL_UNIT_VALUES
)

OPTION_FAMILY_DEFAULT_FACT_KEYS.update(
    (_UNIT_OP_FKEYS[op], "unit", value, CONST_BACKEND.IBIS, None)
    for op in sorted(_UNIT_OP_FKEYS)
    for value in _ALL_UNIT_VALUES
    if value in _IBIS_DUCKDB_DECLARED[op] and value not in {"2d", "3h"}
)


def _datetime_unit_invalid_expr(op: str, value: str):
    return _unit_expr(op, value)


_INVALID_DATETIME_UNIT_REJECTIONS = [
    InvalidOptionRejection(
        _UNIT_OP_FKEYS[op],
        _DATETIME_PROTOCOL,
        op,
        "unit",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda op=op: _datetime_unit_invalid_expr(op, INVALID_OPTION_VALUE),
    )
    for op in sorted(_UNIT_OP_FKEYS)
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_INVALID_DATETIME_UNIT_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _INVALID_DATETIME_UNIT_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize(
    "rejection",
    _INVALID_DATETIME_UNIT_REJECTIONS,
    ids=lambda rejection: f"{rejection.op}-{rejection.param}-{rejection.dtype}",
)
def test_datetime_unit_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


# ============================================================================
# Datetime open-value options: assume_timezone, offset_by, strftime
# ============================================================================

_SUBSTRAIT_DT_PROTOCOL = "SubstraitScalarDatetimeExpressionSystemProtocol"
_MA_DT_PROTOCOL = "MountainAshScalarDatetimeExpressionSystemProtocol"

# 1. assume_timezone
_ASSUME_TZ_DOMAIN = ("UTC", "Australia/Sydney", "America/New_York")


def _assume_tz_expr(tz: str):
    return ma.col("ts").dt.assume_timezone(tz)


def _assume_tz_ref_expr(tz: str):
    ref_tz = "UTC" if tz != "UTC" else "Australia/Sydney"
    return _assume_tz_expr(ref_tz)


def _assume_tz_disposition(backend: str) -> str:
    return "honored" if backend == "polars" else "declared_unsupported"


def _assume_tz_backing_mode(backend: str) -> str:
    return "absence" if backend == "polars" else "class"


def _assume_tz_reason(backend: str) -> str:
    if backend == "polars":
        return "native polars attaches timezone to naive timestamp"
    return (
        "assume_timezone silently drops the timezone (returns a naive timestamp) — "
        "the tz argument is ignored; only polars attaches the timezone"
    )


def _assume_tz_probe(tz: str, backend: str) -> OptionSpec:
    if backend == "polars":
        return OptionSpec(
            FK_DT.ASSUME_TIMEZONE,
            "timezone",
            tz,
            "datetime",
            lambda t=tz: _assume_tz_expr(t),
            lambda t=tz: _assume_tz_ref_expr(t),
            _DATETIME_UNIT_DATA,
            expected_discriminates=True,
        )
    return OptionSpec(
        FK_DT.ASSUME_TIMEZONE,
        "timezone",
        tz,
        "datetime",
        lambda t=tz: _assume_tz_expr(t),
        lambda t=tz: _assume_tz_expr(t),
        _DATETIME_UNIT_DATA,
        expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.ASSUME_TIMEZONE,
        _SUBSTRAIT_DT_PROTOCOL,
        "assume_timezone",
        "timezone",
        backend,
        tz,
        "datetime",
        _assume_tz_disposition(backend),
        _assume_tz_reason(backend),
        _assume_tz_backing_mode(backend),
    )
    for backend in ALL_BACKENDS
    for tz in _ASSUME_TZ_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _assume_tz_probe(tz, backend),
        backend,
        _assume_tz_disposition(backend),
        OptionProbeDidNotDiscriminateError
        if _assume_tz_disposition(backend) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for tz in _ASSUME_TZ_DOMAIN
)

_ASSUME_TZ_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_DT.ASSUME_TIMEZONE,
        _SUBSTRAIT_DT_PROTOCOL,
        "assume_timezone",
        "timezone",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: _assume_tz_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_ASSUME_TZ_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _ASSUME_TZ_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _ASSUME_TZ_INVALID_REJECTIONS)
def test_assume_timezone_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


# 2. offset_by
_OFFSET_BY_DOMAIN = ("1d", "-3mo", "2h30m")


def _offset_by_expr(offset: str):
    return ma.col("ts").dt.offset_by(offset)


def _offset_by_ref_expr(offset: str):
    ref_off = "1d" if offset != "1d" else "2h30m"
    return _offset_by_expr(ref_off)


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_MA_DT.OFFSET_BY,
        _MA_DT_PROTOCOL,
        "offset_by",
        "offset",
        backend,
        offset,
        "datetime",
        "honored",
        "native backend honors offset_by",
        "absence",
    )
    for backend in ALL_BACKENDS
    for offset in _OFFSET_BY_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        OptionSpec(
            FK_MA_DT.OFFSET_BY,
            "offset",
            offset,
            "datetime",
            lambda o=offset: _offset_by_expr(o),
            lambda o=offset: _offset_by_ref_expr(o),
            _DATETIME_UNIT_DATA,
            expected_discriminates=True,
        ),
        backend,
        "honored",
        None,
    )
    for backend in ALL_BACKENDS
    for offset in _OFFSET_BY_DOMAIN
)

_OFFSET_BY_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_MA_DT.OFFSET_BY,
        _MA_DT_PROTOCOL,
        "offset_by",
        "offset",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: _offset_by_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_OFFSET_BY_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _OFFSET_BY_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _OFFSET_BY_INVALID_REJECTIONS)
def test_offset_by_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


# 3. strftime
_STRFTIME_DOMAIN = ("%Y-%m-%d", "%H:%M:%S")


def _strftime_expr(fmt: str):
    return ma.col("ts").dt.strftime(fmt)


def _strftime_ref_expr(fmt: str):
    ref_fmt = "%Y-%m-%d" if fmt != "%Y-%m-%d" else "%H:%M:%S"
    return _strftime_expr(ref_fmt)


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.STRFTIME,
        _SUBSTRAIT_DT_PROTOCOL,
        "strftime",
        "format",
        backend,
        fmt,
        "datetime",
        "honored",
        "native backend honors strftime format",
        "absence",
    )
    for backend in ALL_BACKENDS
    for fmt in _STRFTIME_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        OptionSpec(
            FK_DT.STRFTIME,
            "format",
            fmt,
            "datetime",
            lambda f=fmt: _strftime_expr(f),
            lambda f=fmt: _strftime_ref_expr(f),
            _DATETIME_UNIT_DATA,
            expected_discriminates=True,
        ),
        backend,
        "honored",
        None,
    )
    for backend in ALL_BACKENDS
    for fmt in _STRFTIME_DOMAIN
)


# 4. to_timezone
_TO_TIMEZONE_DOMAIN = ("UTC", "Australia/Sydney", "America/New_York")
_TO_TZ_DATA = {"ts": [datetime(2026, 7, 21, 13, 37, 45, tzinfo=timezone.utc)]}


def _to_tz_expr(tz: str):
    return ma.col("ts").dt.to_timezone(tz).dt.hour()


def _to_tz_ref_expr(tz: str):
    ref_tz = "UTC" if tz != "UTC" else "Australia/Sydney"
    return _to_tz_expr(ref_tz)


def _to_tz_disposition(backend: str) -> str:
    return "declared_unsupported" if backend == "ibis" else "honored"


def _to_tz_backing_mode(backend: str) -> str:
    return "class" if backend == "ibis" else "absence"


def _to_tz_reason(backend: str) -> str:
    if backend == "ibis":
        return (
            "to_timezone is correct only at the materialization boundary -- the "
            "target zone lives in the ibis output dtype, not in the engine (SQL is a "
            "bare CAST AS TIMESTAMPTZ), so any expression composed on the result "
            "raises UnsupportedOperationError"
        )
    return "native backend honors to_timezone"


def _to_tz_probe(tz: str, backend: str) -> OptionSpec:
    if _to_tz_disposition(backend) == "honored":
        return OptionSpec(
            FK_MA_DT.TO_TIMEZONE,
            "timezone",
            tz,
            "datetime",
            lambda t=tz: _to_tz_expr(t),
            lambda t=tz: _to_tz_ref_expr(t),
            _TO_TZ_DATA,
            expected_discriminates=True,
        )
    return OptionSpec(
        FK_MA_DT.TO_TIMEZONE,
        "timezone",
        tz,
        "datetime",
        lambda t=tz: _to_tz_expr(t),
        lambda t=tz: _to_tz_expr(t),
        _TO_TZ_DATA,
        expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_MA_DT.TO_TIMEZONE,
        _MA_DT_PROTOCOL,
        "to_timezone",
        "timezone",
        backend,
        tz,
        "datetime",
        _to_tz_disposition(backend),
        _to_tz_reason(backend),
        _to_tz_backing_mode(backend),
    )
    for backend in ALL_BACKENDS
    for tz in _TO_TIMEZONE_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _to_tz_probe(tz, backend),
        backend,
        _to_tz_disposition(backend),
        BackendCapabilityError
        if _to_tz_disposition(backend) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for tz in _TO_TIMEZONE_DOMAIN
)

_TO_TIMEZONE_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_MA_DT.TO_TIMEZONE,
        _MA_DT_PROTOCOL,
        "to_timezone",
        "timezone",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: _to_tz_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_TO_TIMEZONE_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _TO_TIMEZONE_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _TO_TIMEZONE_INVALID_REJECTIONS)
def test_to_timezone_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


# 5. local_timestamp
_LOCAL_TS_DOMAIN = ("UTC", "Australia/Sydney", "America/New_York")


def _local_ts_expr(tz: str):
    return ma.col("ts").dt.local_timestamp(tz)


def _local_ts_ref_expr(tz: str):
    ref_tz = "UTC" if tz != "UTC" else "Australia/Sydney"
    return _local_ts_expr(ref_tz)


def _local_ts_disposition(backend: str) -> str:
    return "declared_unsupported" if backend == "ibis" else "honored"


def _local_ts_backing_mode(backend: str) -> str:
    return "class" if backend == "ibis" else "absence"


def _local_ts_reason(backend: str) -> str:
    if backend == "ibis":
        return (
            "local_timestamp returns the UTC wall clock, not the target-zone wall "
            "clock -- ibis has no timezone method and the naive re-cast discards the "
            "conversion"
        )
    return "native backend honors local_timestamp"


def _local_ts_probe(tz: str, backend: str) -> OptionSpec:
    if _local_ts_disposition(backend) == "honored":
        return OptionSpec(
            FK_DT.LOCAL_TIMESTAMP,
            "timezone",
            tz,
            "datetime",
            lambda t=tz: _local_ts_expr(t),
            lambda t=tz: _local_ts_ref_expr(t),
            _DATETIME_UNIT_DATA,
            expected_discriminates=True,
        )
    return OptionSpec(
        FK_DT.LOCAL_TIMESTAMP,
        "timezone",
        tz,
        "datetime",
        lambda t=tz: _local_ts_expr(t),
        lambda t=tz: _local_ts_expr(t),
        _DATETIME_UNIT_DATA,
        expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.LOCAL_TIMESTAMP,
        _SUBSTRAIT_DT_PROTOCOL,
        "local_timestamp",
        "timezone",
        backend,
        tz,
        "datetime",
        _local_ts_disposition(backend),
        _local_ts_reason(backend),
        _local_ts_backing_mode(backend),
    )
    for backend in ALL_BACKENDS
    for tz in _LOCAL_TS_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _local_ts_probe(tz, backend),
        backend,
        _local_ts_disposition(backend),
        BackendCapabilityError
        if _local_ts_disposition(backend) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for tz in _LOCAL_TS_DOMAIN
)

_LOCAL_TS_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_DT.LOCAL_TIMESTAMP,
        _SUBSTRAIT_DT_PROTOCOL,
        "local_timestamp",
        "timezone",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: _local_ts_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_LOCAL_TS_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _LOCAL_TS_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _LOCAL_TS_INVALID_REJECTIONS)
def test_local_timestamp_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


# 6. strptime_date / strptime_timestamp
# The format string is an open-domain, unvalidated string. strptime_date is
# declared_unsupported on narwhals-pandas (str.to_date() raises
# NotImplementedError on the default pandas backend); honored elsewhere.
# strptime_timestamp is honored on all four matrix fixtures.
_STRPTIME_DATE_DOMAIN = ("%Y-%m-%d", "%Y-%d-%m")
_STRPTIME_TS_DOMAIN = ("%Y-%m-%d %H:%M:%S", "%Y-%d-%m %H:%M:%S")
_STRPTIME_DATE_DATA = {"s": ["2024-01-05", "2024-02-03", "2024-03-11"]}
_STRPTIME_TS_DATA = {"s": ["2024-01-05 06:07:08", "2024-02-03 09:10:11", "2024-03-11 12:13:14"]}


def _strptime_date_expr(fmt: str):
    return ma.col("s").str.to_date(fmt)


def _strptime_date_ref_expr(fmt: str):
    ref = "%Y-%m-%d" if fmt != "%Y-%m-%d" else "%Y-%d-%m"
    return _strptime_date_expr(ref)


def _strptime_date_disposition(backend: str) -> str:
    return "declared_unsupported" if backend == "narwhals-pandas" else "honored"


def _strptime_date_backing_mode(backend: str) -> str:
    return "op-level" if backend == "narwhals-pandas" else "absence"


def _strptime_date_reason(backend: str) -> str:
    if backend == "narwhals-pandas":
        return (
            "narwhals raises NotImplementedError for str.to_date() on the default "
            "pandas backend; the whole op is gated op-level rather than per-value"
        )
    return "native backend honors strptime_date format"


def _strptime_date_probe(fmt: str, backend: str) -> OptionSpec:
    if _strptime_date_disposition(backend) == "honored":
        return OptionSpec(
            FK_DT.STRPTIME_DATE,
            "format",
            fmt,
            "str",
            lambda f=fmt: _strptime_date_expr(f),
            lambda f=fmt: _strptime_date_ref_expr(f),
            _STRPTIME_DATE_DATA,
            expected_discriminates=True,
        )
    return OptionSpec(
        FK_DT.STRPTIME_DATE,
        "format",
        fmt,
        "str",
        lambda f=fmt: _strptime_date_expr(f),
        lambda f=fmt: _strptime_date_expr(f),
        _STRPTIME_DATE_DATA,
        expected_discriminates=True,
    )


def _strptime_ts_expr(fmt: str):
    return ma.col("s").str.to_datetime(fmt)


def _strptime_ts_ref_expr(fmt: str):
    ref = "%Y-%m-%d %H:%M:%S" if fmt != "%Y-%m-%d %H:%M:%S" else "%Y-%d-%m %H:%M:%S"
    return _strptime_ts_expr(ref)


def _strptime_ts_probe(fmt: str, backend: str) -> OptionSpec:
    return OptionSpec(
        FK_DT.STRPTIME_TIMESTAMP,
        "format",
        fmt,
        "str",
        lambda f=fmt: _strptime_ts_expr(f),
        lambda f=fmt: _strptime_ts_ref_expr(f),
        _STRPTIME_TS_DATA,
        expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.STRPTIME_DATE,
        _SUBSTRAIT_DT_PROTOCOL,
        "strptime_date",
        "format",
        backend,
        fmt,
        "str",
        _strptime_date_disposition(backend),
        _strptime_date_reason(backend),
        _strptime_date_backing_mode(backend),
    )
    for backend in ALL_BACKENDS
    for fmt in _STRPTIME_DATE_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _strptime_date_probe(fmt, backend),
        backend,
        _strptime_date_disposition(backend),
        NotImplementedError
        if _strptime_date_disposition(backend) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for fmt in _STRPTIME_DATE_DOMAIN
)

OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.STRPTIME_TIMESTAMP,
        _SUBSTRAIT_DT_PROTOCOL,
        "strptime_timestamp",
        "format",
        backend,
        fmt,
        "str",
        "honored",
        "native backend honors strptime_timestamp format",
        "absence",
    )
    for backend in ALL_BACKENDS
    for fmt in _STRPTIME_TS_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _strptime_ts_probe(fmt, backend),
        backend,
        "honored",
        None,
    )
    for backend in ALL_BACKENDS
    for fmt in _STRPTIME_TS_DOMAIN
)

# 7. strptime_timestamp.timezone (item 62 — end-to-end wiring)
_STRPTIME_TS_TZ_DOMAIN = ("UTC", "Australia/Sydney", "America/New_York")
_STRPTIME_TS_TZ_DATA = {"s": ["2024-01-05 06:07:08"]}


def _strptime_ts_tz_expr(tz: str):
    return ma.col("s").str.to_datetime("%Y-%m-%d %H:%M:%S", timezone=tz)


def _strptime_ts_tz_ref_expr(tz: str):
    ref = "UTC" if tz != "UTC" else "Australia/Sydney"
    return _strptime_ts_tz_expr(ref)


def _strptime_ts_tz_disposition(backend: str) -> str:
    return "declared_unsupported" if backend == "ibis" else "honored"


def _strptime_ts_tz_probe(tz: str, backend: str) -> OptionSpec:
    if _strptime_ts_tz_disposition(backend) == "honored":
        return OptionSpec(
            FK_DT.STRPTIME_TIMESTAMP, "timezone", tz, "str",
            lambda t=tz: _strptime_ts_tz_expr(t),
            lambda t=tz: _strptime_ts_tz_ref_expr(t),
            _STRPTIME_TS_TZ_DATA, expected_discriminates=True,
        )
    return OptionSpec(
        FK_DT.STRPTIME_TIMESTAMP, "timezone", tz, "str",
        lambda t=tz: _strptime_ts_tz_expr(t),
        lambda t=tz: _strptime_ts_tz_expr(t),
        _STRPTIME_TS_TZ_DATA, expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.STRPTIME_TIMESTAMP,
        _SUBSTRAIT_DT_PROTOCOL,
        "strptime_timestamp",
        "timezone",
        backend,
        tz,
        "str",
        _strptime_ts_tz_disposition(backend),
        (
            "ibis has no timezone primitives; the timezone option is silently ignored"
            if backend == "ibis"
            else "native backend attaches the parsed timezone"
        ),
        "class" if backend == "ibis" else "absence",
    )
    for backend in ALL_BACKENDS
    for tz in _STRPTIME_TS_TZ_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _strptime_ts_tz_probe(tz, backend),
        backend,
        _strptime_ts_tz_disposition(backend),
        OptionProbeDidNotDiscriminateError
        if _strptime_ts_tz_disposition(backend) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for tz in _STRPTIME_TS_TZ_DOMAIN
)

_STRPTIME_TS_TZ_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_DT.STRPTIME_TIMESTAMP,
        _SUBSTRAIT_DT_PROTOCOL,
        "strptime_timestamp",
        "timezone",
        INVALID_OPTION_VALUE,
        "str",
        lambda: _strptime_ts_tz_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_STRPTIME_TS_TZ_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _STRPTIME_TS_TZ_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _STRPTIME_TS_TZ_INVALID_REJECTIONS)
def test_strptime_timestamp_timezone_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()



# ============================================================================
# extract / extract_boolean (item 62)
# ============================================================================

_EXTRACT_COMPONENT_DOMAIN = tuple(c.value for c in DatetimeComponent)
_EXTRACT_BOOL_COMPONENT_DOMAIN = tuple(c.value for c in BooleanComponent)
_EXTRACT_INDEXING_DOMAIN = ("ONE", "ZERO")
_EXTRACT_TZ_DOMAIN = ("UTC", "Australia/Sydney", "America/New_York")
# Boundary data: Jan 1 00:30 interpreted as UTC flips to Dec 31 of the prior
# year in America/New_York, so IS_LEAP_YEAR(timezone=...) discriminates across
# zones (2024 leap vs 2023 non-leap).
_EXTRACT_BOOL_TZ_DATA = {"ts": [datetime(2024, 1, 1, 0, 30, 0)]}

# Per-backend component sets the native backend cannot produce (probe-authoritative).
_EXTRACT_DECLARED = {
    "polars": frozenset(
        {"US_YEAR", "MONDAY_WEEK", "SUNDAY_WEEK", "US_WEEK", "PICOSECOND", "TIMEZONE_OFFSET"}
    ),
    "ibis": frozenset(
        {
            "US_YEAR", "MONDAY_WEEK", "SUNDAY_WEEK", "US_WEEK",
            "NANOSECOND", "PICOSECOND", "TIMEZONE_OFFSET",
        }
    ),
    "narwhals-polars": frozenset(
        {
            "ISO_YEAR", "US_YEAR", "MONDAY_WEEK", "SUNDAY_WEEK", "ISO_WEEK",
            "US_WEEK", "PICOSECOND", "UNIX_TIME", "TIMEZONE_OFFSET",
        }
    ),
    "narwhals-pandas": frozenset(
        {
            "ISO_YEAR", "US_YEAR", "MONDAY_WEEK", "SUNDAY_WEEK", "ISO_WEEK",
            "US_WEEK", "PICOSECOND", "UNIX_TIME", "TIMEZONE_OFFSET",
        }
    ),
}


def _extract_expr(comp: str):
    return ma.col("ts").dt.extract(comp)


def _extract_ref_expr(comp: str):
    # Reference component chosen to differ from every honored component on the
    # probe fixture (month=7/day=21 never collide with year/week/… values).
    return _extract_expr("MONTH" if comp != "MONTH" else "DAY")


def _extract_disposition(backend: str, comp: str) -> str:
    return "declared_unsupported" if comp in _EXTRACT_DECLARED[backend] else "honored"


def _extract_component_probe(comp: str, backend: str) -> OptionSpec:
    if _extract_disposition(backend, comp) == "honored":
        return OptionSpec(
            FK_DT.EXTRACT, "component", comp, "datetime",
            lambda c=comp: _extract_expr(c),
            lambda c=comp: _extract_ref_expr(c),
            _DATETIME_UNIT_DATA, expected_discriminates=True,
        )
    return OptionSpec(
        FK_DT.EXTRACT, "component", comp, "datetime",
        lambda c=comp: _extract_expr(c),
        lambda c=comp: _extract_expr(c),
        _DATETIME_UNIT_DATA, expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.EXTRACT,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "component",
        backend,
        comp,
        "datetime",
        _extract_disposition(backend, comp),
        (
            "native backend has no primitive for this extract component "
            "(probe-authoritative)"
            if _extract_disposition(backend, comp) == "declared_unsupported"
            else "native backend honors this extract component"
        ),
        "absence",
    )
    for backend in ALL_BACKENDS
    for comp in _EXTRACT_COMPONENT_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _extract_component_probe(comp, backend),
        backend,
        _extract_disposition(backend, comp),
        BackendCapabilityError
        if _extract_disposition(backend, comp) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for comp in _EXTRACT_COMPONENT_DOMAIN
)

OPTION_FAMILY_DEFAULT_FACT_KEYS.update(
    (FK_DT.EXTRACT, "component", comp, CONST_BACKEND.IBIS, None)
    for comp in sorted(_EXTRACT_DECLARED["ibis"])
)
OPTION_FAMILY_DEFAULT_FACT_KEYS.add(
    (FK_DT.EXTRACT_BOOLEAN, "component", "IS_DST", CONST_BACKEND.IBIS, None)
)

_EXTRACT_COMPONENT_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_DT.EXTRACT,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "component",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: _extract_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_EXTRACT_COMPONENT_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _EXTRACT_COMPONENT_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _EXTRACT_COMPONENT_INVALID_REJECTIONS)
def test_extract_component_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


def _extract_indexing_expr(idx: str):
    return ma.col("ts").dt.extract("MONTH", indexing=idx)


def _extract_indexing_probe(idx: str) -> OptionSpec:
    return OptionSpec(
        FK_DT.EXTRACT, "indexing", idx, "datetime",
        lambda i=idx: _extract_indexing_expr(i),
        lambda: ma.col("ts").dt.extract("MONTH"),
        _DATETIME_UNIT_DATA,
        expected_discriminates=(idx == "ZERO"),
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.EXTRACT,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "indexing",
        backend,
        idx,
        "datetime",
        "honored",
        "ONE is the native 1-based default; ZERO subtracts one on calendar components",
        "absence",
    )
    for backend in ALL_BACKENDS
    for idx in _EXTRACT_INDEXING_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _extract_indexing_probe(idx),
        backend,
        "honored",
        None,
    )
    for backend in ALL_BACKENDS
    for idx in _EXTRACT_INDEXING_DOMAIN
)

_EXTRACT_INDEXING_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_DT.EXTRACT,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "indexing",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: _extract_indexing_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_EXTRACT_INDEXING_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _EXTRACT_INDEXING_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _EXTRACT_INDEXING_INVALID_REJECTIONS)
def test_extract_indexing_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


def _extract_tz_expr(tz: str):
    return ma.col("ts").dt.extract("HOUR", timezone=tz)


def _extract_tz_ref_expr(tz: str):
    ref = "UTC" if tz != "UTC" else "Australia/Sydney"
    return _extract_tz_expr(ref)


def _extract_tz_disposition(backend: str) -> str:
    return "declared_unsupported" if backend == "ibis" else "honored"


def _extract_tz_probe(tz: str, backend: str) -> OptionSpec:
    if _extract_tz_disposition(backend) == "honored":
        return OptionSpec(
            FK_DT.EXTRACT, "timezone", tz, "datetime",
            lambda t=tz: _extract_tz_expr(t),
            lambda t=tz: _extract_tz_ref_expr(t),
            _DATETIME_UNIT_DATA, expected_discriminates=True,
        )
    return OptionSpec(
        FK_DT.EXTRACT, "timezone", tz, "datetime",
        lambda t=tz: _extract_tz_expr(t),
        lambda t=tz: _extract_tz_expr(t),
        _DATETIME_UNIT_DATA, expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.EXTRACT,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "timezone",
        backend,
        tz,
        "datetime",
        _extract_tz_disposition(backend),
        (
            "ibis has no timezone primitives; the timezone option is silently ignored"
            if backend == "ibis"
            else "native backend converts to the target zone before the component lookup"
        ),
        "class" if backend == "ibis" else "absence",
    )
    for backend in ALL_BACKENDS
    for tz in _EXTRACT_TZ_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _extract_tz_probe(tz, backend),
        backend,
        _extract_tz_disposition(backend),
        OptionProbeDidNotDiscriminateError
        if _extract_tz_disposition(backend) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for tz in _EXTRACT_TZ_DOMAIN
)

_EXTRACT_TZ_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_DT.EXTRACT,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "timezone",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: _extract_tz_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_EXTRACT_TZ_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _EXTRACT_TZ_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _EXTRACT_TZ_INVALID_REJECTIONS)
def test_extract_timezone_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


def _extract_boolean_expr(comp: str):
    if comp == "IS_DST":
        return ma.col("ts").dt.extract_boolean("IS_DST", timezone="UTC")
    return ma.col("ts").dt.extract_boolean(comp)


def _extract_boolean_disposition(comp: str) -> str:
    return "declared_unsupported" if comp == "IS_DST" else "honored"


def _extract_boolean_component_probe(comp: str, backend: str) -> OptionSpec:
    if _extract_boolean_disposition(comp) == "honored":
        return OptionSpec(
            FK_DT.EXTRACT_BOOLEAN, "component", comp, "datetime",
            lambda c=comp: _extract_boolean_expr(c),
            lambda: ma.col("ts").dt.extract("MONTH"),
            _DATETIME_UNIT_DATA, expected_discriminates=True,
        )
    return OptionSpec(
        FK_DT.EXTRACT_BOOLEAN, "component", comp, "datetime",
        lambda c=comp: _extract_boolean_expr(c),
        lambda c=comp: _extract_boolean_expr(c),
        _DATETIME_UNIT_DATA, expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.EXTRACT_BOOLEAN,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract_boolean",
        "component",
        backend,
        comp,
        "datetime",
        _extract_boolean_disposition(comp),
        (
            "IS_DST is a placeholder (constant False); deferred to backlog item 65"
            if comp == "IS_DST"
            else "native backend honors IS_LEAP_YEAR"
        ),
        "absence",
    )
    for backend in ALL_BACKENDS
    for comp in _EXTRACT_BOOL_COMPONENT_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _extract_boolean_component_probe(comp, backend),
        backend,
        _extract_boolean_disposition(comp),
        BackendCapabilityError
        if _extract_boolean_disposition(comp) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for comp in _EXTRACT_BOOL_COMPONENT_DOMAIN
)

_EXTRACT_BOOL_COMPONENT_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_DT.EXTRACT_BOOLEAN,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract_boolean",
        "component",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: ma.col("ts").dt.extract_boolean(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_EXTRACT_BOOL_COMPONENT_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _EXTRACT_BOOL_COMPONENT_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _EXTRACT_BOOL_COMPONENT_INVALID_REJECTIONS)
def test_extract_boolean_component_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


def _extract_bool_tz_expr(tz: str):
    return ma.col("ts").dt.extract_boolean("IS_LEAP_YEAR", timezone=tz)


def _extract_bool_tz_ref_expr(tz: str):
    ref = "America/New_York" if tz != "America/New_York" else "UTC"
    return _extract_bool_tz_expr(ref)


def _extract_bool_tz_probe(tz: str, backend: str) -> OptionSpec:
    if backend == "ibis":
        return OptionSpec(
            FK_DT.EXTRACT_BOOLEAN, "timezone", tz, "datetime",
            lambda t=tz: _extract_bool_tz_expr(t),
            lambda t=tz: _extract_bool_tz_expr(t),
            _EXTRACT_BOOL_TZ_DATA, expected_discriminates=True,
        )
    return OptionSpec(
        FK_DT.EXTRACT_BOOLEAN, "timezone", tz, "datetime",
        lambda t=tz: _extract_bool_tz_expr(t),
        lambda t=tz: _extract_bool_tz_ref_expr(t),
        _EXTRACT_BOOL_TZ_DATA, expected_discriminates=True,
    )


OPTION_DISPOSITIONS.extend(
    OptionCell(
        FK_DT.EXTRACT_BOOLEAN,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract_boolean",
        "timezone",
        backend,
        tz,
        "datetime",
        _extract_tz_disposition(backend),
        (
            "ibis has no timezone primitives; the timezone option is silently ignored"
            if backend == "ibis"
            else "native backend converts to the target zone before the boolean lookup"
        ),
        "class" if backend == "ibis" else "absence",
    )
    for backend in ALL_BACKENDS
    for tz in _EXTRACT_TZ_DOMAIN
)

REGISTERED_OPTION_PROBES.extend(
    OptionProbeRegistration(
        _extract_bool_tz_probe(tz, backend),
        backend,
        _extract_tz_disposition(backend),
        OptionProbeDidNotDiscriminateError
        if _extract_tz_disposition(backend) == "declared_unsupported"
        else None,
    )
    for backend in ALL_BACKENDS
    for tz in _EXTRACT_TZ_DOMAIN
)

_EXTRACT_BOOL_TZ_INVALID_REJECTIONS = [
    InvalidOptionRejection(
        FK_DT.EXTRACT_BOOLEAN,
        _SUBSTRAIT_DT_PROTOCOL,
        "extract_boolean",
        "timezone",
        INVALID_OPTION_VALUE,
        "datetime",
        lambda: _extract_bool_tz_expr(INVALID_OPTION_VALUE),
    )
]
REGISTERED_INVALID_OPTION_REJECTIONS.extend(_EXTRACT_BOOL_TZ_INVALID_REJECTIONS)
OPTION_DISPOSITIONS.extend(
    OptionCell(
        rejection.fkey,
        rejection.protocol,
        rejection.op,
        rejection.param,
        backend,
        rejection.value,
        rejection.dtype,
        "invalid",
        "canonical build-time rejection sentinel; invalid strings are unbounded",
        "absence",
    )
    for rejection in _EXTRACT_BOOL_TZ_INVALID_REJECTIONS
    for backend in ALL_BACKENDS
)


@pytest.mark.parametrize("rejection", _EXTRACT_BOOL_TZ_INVALID_REJECTIONS)
def test_extract_boolean_timezone_invalid_option_rejected_at_build_time(
    rejection: InvalidOptionRejection,
) -> None:
    with pytest.raises(InvalidOptionValueError):
        rejection.build_expr()


def test_is_dst_requires_timezone() -> None:
    with pytest.raises(InvalidOptionValueError):
        ma.col("ts").dt.is_dst()


TESTED_OPTION_PARAMS: list[tuple] = []
TESTED_OPTION_PARAMS.extend(
    (
        _DATETIME_PROTOCOL,
        op,
        "unit",
        param_taxonomy(_DATETIME_PROTOCOL, op, "unit"),
    )
    for op in sorted(_UNIT_OP_FKEYS)
)
TESTED_OPTION_PARAMS.extend([
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "assume_timezone",
        "timezone",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "assume_timezone", "timezone"),
    ),
    (
        _MA_DT_PROTOCOL,
        "offset_by",
        "offset",
        param_taxonomy(_MA_DT_PROTOCOL, "offset_by", "offset"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "strftime",
        "format",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "strftime", "format"),
    ),
    (
        _MA_DT_PROTOCOL,
        "to_timezone",
        "timezone",
        param_taxonomy(_MA_DT_PROTOCOL, "to_timezone", "timezone"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "local_timestamp",
        "timezone",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "local_timestamp", "timezone"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "strptime_date",
        "format",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "strptime_date", "format"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "strptime_timestamp",
        "format",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "strptime_timestamp", "format"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "strptime_timestamp",
        "timezone",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "strptime_timestamp", "timezone"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "component",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "extract", "component"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "indexing",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "extract", "indexing"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "extract",
        "timezone",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "extract", "timezone"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "extract_boolean",
        "component",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "extract_boolean", "component"),
    ),
    (
        _SUBSTRAIT_DT_PROTOCOL,
        "extract_boolean",
        "timezone",
        param_taxonomy(_SUBSTRAIT_DT_PROTOCOL, "extract_boolean", "timezone"),
    ),
])


