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
- to_timezone.timezone: FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE is not in the
  Polars function registry (KeyError at compile time).
- assume_timezone.timezone, strftime.format, truncate.unit, ceil.unit, floor.unit,
  round.unit: these are passed as options (not visited expressions) in the API builder;
  lit/col/complex input types fail with TypeError.  ceil/floor/round are additionally
  broken even with raw args (name collision with numeric rounding).
- extract.component, extract.timezone, extract_boolean.component: internal dispatch
  params used by the visitor, not exposed via the fluent API.
- round_temporal.*, round_calendar.*: options (int/str literals), not expression args.
"""
from __future__ import annotations

from datetime import datetime

import pytest

import mountainash as ma
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME as FK_DT,
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_MA_DT,
)
from cross_backend.argument_types.conftest import ALL_BACKENDS
from cross_backend.argument_types._test_template import (
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
    (FK_MA_DT.ASSUME_TIMEZONE, "timezone"),
    (FK_MA_DT.ASSUME_TIMEZONE, "x"),
    (FK_MA_DT.CEIL, "unit"),
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
    (FK_DT.EXTRACT, "component"),
    (FK_DT.EXTRACT, "timezone"),
    (FK_DT.EXTRACT, "x"),
    (FK_DT.EXTRACT_BOOLEAN, "component"),
    (FK_DT.EXTRACT_BOOLEAN, "x"),
    (FK_MA_DT.FLOOR, "unit"),
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
    (FK_MA_DT.ROUND, "unit"),
    (FK_MA_DT.ROUND, "x"),
    ("round_calendar", "multiple"),
    ("round_calendar", "origin"),
    ("round_calendar", "rounding"),
    ("round_calendar", "unit"),
    ("round_calendar", "x"),
    ("round_temporal", "multiple"),
    ("round_temporal", "origin"),
    ("round_temporal", "rounding"),
    ("round_temporal", "unit"),
    ("round_temporal", "x"),
    ("second", "x"),
    (FK_MA_DT.STRFTIME, "format"),
    (FK_MA_DT.STRFTIME, "x"),
    ("strptime_date", "x"),
    ("strptime_time", "x"),
    ("strptime_timestamp", "x"),
    ("subtract", "x"),
    ("subtract", "y"),
    ("timezone_offset", "x"),
    (FK_MA_DT.TO_TIMEZONE, "timezone"),
    (FK_MA_DT.TO_TIMEZONE, "x"),
    (FK_MA_DT.TRUNCATE, "unit"),
    (FK_MA_DT.TRUNCATE, "x"),
    ("unix_timestamp", "x"),
    ("week_of_year", "x"),
    ("year", "x"),
    (FK_MA_DT.TOTAL_SECONDS, "x"),
    (FK_MA_DT.TOTAL_MINUTES, "x"),
    (FK_MA_DT.TOTAL_MILLISECONDS, "x"),
    (FK_MA_DT.TOTAL_MICROSECONDS, "x"),
]

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
]


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ALL_BACKENDS:
            for it in INPUT_TYPES:
                mark = xfail_if_limited(bk, op.function_key, op.param_name, it)
                marks = [mark] if mark else []
                cases.append(
                    pytest.param(op, bk, it, marks=marks, id=f"{op.op_name}-{bk}-{it}")
                )
    return cases


if OP_SPECS:

    @pytest.mark.parametrize("op,backend,input_type", _params())
    def test_argument_channel(op: OpSpec, backend: str, input_type: str):
        run_argument_matrix(op, backend, input_type)
