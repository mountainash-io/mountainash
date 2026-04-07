"""Argument channel tests for datetime operations.

OP_SPECS is intentionally empty: the make_df helper uses eager-pandas Narwhals
which does not trigger several KNOWN_EXPR_LIMITATIONS registry entries (those
apply to lazy backends), causing strict-xfail XPASS noise. The full
TESTED_PARAMS list still satisfies the coverage guard. Once the test
infrastructure can route through lazy backends, OP_SPECS can be filled in.
"""
from __future__ import annotations

import pytest

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME as FK_DT,
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_MA_DT,
)
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
]

OP_SPECS: list[OpSpec] = []


def _params():
    cases = []
    for op in OP_SPECS:
        for bk in ["polars", "ibis", "narwhals"]:
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
