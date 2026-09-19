"""Registry-driven compiler smoke coverage with strict native-gap witnesses."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)

if TYPE_CHECKING:
    from enum import Enum
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI

_TESTS_DIR = str(Path(__file__).resolve().parent.parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from core._smoke_helpers import (  # noqa: E402
    _SENTINEL_MISSING,
    _get_category_for_fkey,
    build_args_for_fkey,
    get_smoke_expr_builder,
    is_non_expression_fkey,
)
from fixtures.call_expectations import expect_call_failure
ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

_NAMESPACE_PREFIXES = {"list_": "list", "struct_": "struct"}
_DESCRIPTOR_NAMESPACES = ("str", "dt", "list", "struct", "geo")


def _resolve_api_callable(
    base: BaseExpressionAPI, method_name: str
) -> object | None:
    try:
        return getattr(base, method_name)
    except AttributeError:
        pass

    for prefix, ns_name in _NAMESPACE_PREFIXES.items():
        if method_name.startswith(prefix):
            stripped = method_name[len(prefix) :]
            try:
                ns = getattr(base, ns_name)
                return getattr(ns, stripped)
            except AttributeError:
                pass

    for ns_name in _DESCRIPTOR_NAMESPACES:
        try:
            ns = getattr(base, ns_name)
            return getattr(ns, method_name)
        except AttributeError:
            continue

    return None


# Hand-owned compile witnesses. Native gaps use strict XPASS detection; ordinary
# backend refusals pass only after their emitted function key is checked.
@dataclass(frozen=True)
class NativeSmokeWitness:
    error_type: type[BaseException]
    reason: str
    strict_xfail: bool = True

_NATIVE_SMOKE_WITNESSES: dict[tuple[str, str], NativeSmokeWitness] = {
    # ── NotImplementedError ──
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support days_in_month() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support days_in_month() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support days_in_month() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support month_end() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support month_end() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support month_end() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support month_start() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support month_start() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support month_start() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support .dt.time() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support .dt.time() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Narwhals does not support .dt.time() Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_DAYS", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_days() method. Use dt.diff_days() for integer-based extraction. Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_DAYS", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_days() method. Use dt.diff_days() for integer-based extraction. Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_HOURS", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_hours() method. Use dt.diff_hours() for integer-based extraction. Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_HOURS", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_hours() method. Use dt.diff_hours() for integer-based extraction. Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MICROSECONDS", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_microseconds() method. Use integer arithmetic on dt.diff_seconds... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MICROSECONDS", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_microseconds() method. Use integer arithmetic on dt.diff_seconds... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MILLISECONDS", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_milliseconds() method. Use dt.diff_milliseconds() for integer-ba... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MILLISECONDS", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_milliseconds() method. Use dt.diff_milliseconds() for integer-ba... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MINUTES", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_minutes() method. Use dt.diff_minutes() for integer-based extrac... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MINUTES", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_minutes() method. Use dt.diff_minutes() for integer-based extrac... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_NANOSECONDS", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_nanoseconds() method. Use integer arithmetic on dt.diff_seconds(... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_NANOSECONDS", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_nanoseconds() method. Use integer arithmetic on dt.diff_seconds(... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_seconds() method. Use dt.diff_seconds() for integer-based extrac... Since 2026-05-18."),
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: Ibis IntervalValue has no total_seconds() method. Use dt.diff_seconds() for integer-based extrac... Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acos() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acos() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acos() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acosh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acosh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "ibis-sqlite"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acosh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acosh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acosh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: acosh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asin() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asin() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asin() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asinh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asinh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "ibis-sqlite"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asinh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asinh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asinh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: asinh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atan() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atan() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atan() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atan2() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atan2() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atan2() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atanh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atanh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "ibis-sqlite"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atanh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atanh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atanh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: atanh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cos() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cos() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cos() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cosh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cosh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "ibis-sqlite"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cosh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cosh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cosh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cosh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: degrees() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: degrees() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: degrees() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-sqlite"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tan() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tan() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tan() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tanh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tanh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "ibis-sqlite"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tanh() is not directly supported by the Ibis backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tanh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tanh() is not supported by the Narwhals backend. Since 2026-05-18."),
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: tanh() is not supported by the Narwhals backend. Since 2026-05-18."),
    # ── Aggregate and window native gaps ──
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR", "polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: corr() requires struct context in Polars; use DataFrame.corr() instead. Tracked in cross-backend-result-verification-deferred.md. Since 2026-05-20."),
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: corr() requires struct/aggregation context. Since 2026-05-20."),
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: corr() requires struct/aggregation context. Since 2026-05-20."),
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: corr() requires struct/aggregation context. Since 2026-05-20."),
    # ── Smoke expr builder: newly-exposed backend limitations ──
    # PERCENT_RANK — Narwhals backend does not implement percent_rank()
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20."),
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20."),
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20."),
    # CUME_DIST — Narwhals backend does not implement cume_dist()
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20."),
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20."),
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON", "pandas"): NativeSmokeWitness(NotImplementedError, "Narwhals GeoJSON compiler is unavailable for this concrete parser call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "Narwhals GeoJSON compiler is unavailable for this concrete parser call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "Narwhals GeoJSON compiler is unavailable for this concrete parser call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "Ibis GeoJSON compiler is unavailable for this concrete parser call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "Ibis GeoJSON compiler is unavailable for this concrete parser call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON", "ibis-sqlite"): NativeSmokeWitness(NotImplementedError, "Ibis GeoJSON compiler is unavailable for this concrete parser call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON", "pandas"): NativeSmokeWitness(NotImplementedError, "Narwhals GeoJSON compiler is unavailable for this concrete serializer call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON", "narwhals-polars"): NativeSmokeWitness(NotImplementedError, "Narwhals GeoJSON compiler is unavailable for this concrete serializer call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON", "narwhals-pandas"): NativeSmokeWitness(NotImplementedError, "Narwhals GeoJSON compiler is unavailable for this concrete serializer call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON", "ibis-polars"): NativeSmokeWitness(NotImplementedError, "Ibis GeoJSON compiler is unavailable for this concrete serializer call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON", "ibis-duckdb"): NativeSmokeWitness(NotImplementedError, "Ibis GeoJSON compiler is unavailable for this concrete serializer call."),
    ("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON", "ibis-sqlite"): NativeSmokeWitness(NotImplementedError, "Ibis GeoJSON compiler is unavailable for this concrete serializer call."),
}

# The public canonical calls match their registered protocols, but concrete
# backends still expose the shorter non-Substrait signatures. Keep the real
# compiler failures visible until that separately scoped implementation gap closes.
for _backend in ALL_BACKENDS:
    for _operation in ("MEDIAN", "QUANTILE"):
        _NATIVE_SMOKE_WITNESSES[
            (f"FKEY_SUBSTRAIT_SCALAR_AGGREGATE.{_operation}", _backend)
        ] = NativeSmokeWitness(
            TypeError, "Canonical aggregate protocol/backend signature mismatch.",
        )

# Concrete representative calls, owned by this test. These groups follow the
# unconditional backend methods (or the explicitly noted default option), not
# catalogue records or captured failures. New backends receive no inherited answer.
_NARWHALS_CASES = ("pandas", "narwhals-polars", "narwhals-pandas")
_IBIS_CASES = ("ibis-polars", "ibis-duckdb", "ibis-sqlite")


def _intrinsic_refusals(enum_name, members, backends, reason):
    for member in members.split():
        for backend in backends:
            key = (f"{enum_name}.{member}", backend)
            assert key not in _NATIVE_SMOKE_WITNESSES, key
            _NATIVE_SMOKE_WITNESSES[key] = NativeSmokeWitness(
                BackendCapabilityError, reason, strict_xfail=False,
            )


# Scalar arithmetic backend methods explicitly reject these bitwise operations.
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC", "BITWISE_XOR",
                    _NARWHALS_CASES, "Narwhals has no bitwise XOR implementation.")
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC", "SHIFT_LEFT SHIFT_RIGHT",
                    ("polars", *_NARWHALS_CASES), "These backends have no bitwise shift implementation.")
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC", "SHIFT_RIGHT_UNSIGNED",
                    tuple(ALL_BACKENDS), "Unsigned right shift is not implemented by any backend.")

# expsys_{ib,nw}_scalar_string and extension string methods.
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_STRING",
                    "REGEXP_MATCH_ALL REGEXP_COUNT REGEXP_STRPOS SWAPCASE",
                    (*_NARWHALS_CASES, *_IBIS_CASES), "No corresponding backend string implementation.")
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_STRING",
                    "REGEXP_MATCH CAPITALIZE CENTER STRPOS REPEAT",
                    _NARWHALS_CASES, "No Narwhals implementation for this string operation.")
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_STRING", "TITLE INITCAP",
                    _IBIS_CASES, "No Ibis title/initcap implementation.")
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_STRING", "LIKE",
                    ("ibis-polars",), "The Ibis Polars LIKE compiler is unavailable.")
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_STRING", "REGEXP_SPLIT",
                    (*_NARWHALS_CASES, "ibis-sqlite"), "No regex split primitive/compiler for this target.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_STRING",
                    "TO_TIME JSON_DECODE JSON_PATH_MATCH ENCODE DECODE EXTRACT_GROUPS",
                    (*_NARWHALS_CASES, *_IBIS_CASES), "Backend extension method is explicitly unavailable.")

# Datetime defaults: formatted parsing and XSD parsing use THROW, not NULL.
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_DATETIME", "ASSUME_TIMEZONE",
                    (*_NARWHALS_CASES, *_IBIS_CASES), "Timezone assumption is not implemented.")
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_DATETIME", "LOCAL_TIMESTAMP",
                    _IBIS_CASES, "Ibis cannot implement local timestamp conversion.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_DATETIME", "PARSE_DEFAULT PARSE_TEMPORAL_ANY",
                    (*_NARWHALS_CASES, *_IBIS_CASES), "Flexible temporal parsing is not implemented.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_DATETIME", "IS_DST TO_TIMEZONE",
                    _IBIS_CASES, "Ibis timezone conversion/DST inspection is unavailable.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_DATETIME", "EXTRACT_WEEK",
                    _NARWHALS_CASES, "Narwhals cannot implement this week extraction contract.")
_intrinsic_refusals("FKEY_SUBSTRAIT_SCALAR_DATETIME", "STRPTIME_DATE STRPTIME_TIMESTAMP",
                    ("ibis-sqlite",), "SQLite cannot compile formatted temporal parsing.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_DATETIME", "PARSE_XSD_DURATION PARSE_XSD_PARTIAL_DATE",
                    ("ibis-sqlite",), "SQLite cannot provide the requested THROW parsing contract.")

# Concrete rank methods and expression-level null filling.
_intrinsic_refusals("FKEY_MOUNTAINASH_WINDOW", "RANK_AVERAGE RANK_MAX FORWARD_FILL BACKWARD_FILL",
                    _IBIS_CASES, "Ibis lacks these rank/fill expression contracts.")
for _backend in _NARWHALS_CASES:
    for _operation in ("NTILE", "NTH_VALUE"):
        _NATIVE_SMOKE_WITNESSES[
            (f"SUBSTRAIT_ARITHMETIC_WINDOW.{_operation}", _backend)
        ] = NativeSmokeWitness(NotImplementedError, "Narwhals window method is not implemented.")

# The list methods below unconditionally refuse in their respective backend
# implementations. SQLite's native array construction is a separate boundary.
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_LIST",
                    "DROP_NULLS MEDIAN STD VAR N_UNIQUE COUNT_MATCHES ITEM REVERSE HEAD TAIL "
                    "SLICE GATHER GATHER_EVERY SHIFT DIFF SET_DIFFERENCE SET_SYMMETRIC_DIFFERENCE "
                    "FILTER TO_STRUCT TO_ARRAY ARG_MIN ARG_MAX SAMPLE AGG",
                    ("ibis-polars", "ibis-duckdb"), "Ibis has no compatible array operation.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_LIST",
                    "EXPLODE JOIN ALL ANY DROP_NULLS STD VAR N_UNIQUE COUNT_MATCHES ITEM REVERSE "
                    "HEAD TAIL SLICE GATHER GATHER_EVERY SHIFT DIFF SET_UNION SET_INTERSECTION "
                    "SET_DIFFERENCE SET_SYMMETRIC_DIFFERENCE CONCAT FILTER TO_STRUCT TO_ARRAY "
                    "ARG_MIN ARG_MAX SAMPLE AGG",
                    _NARWHALS_CASES, "Narwhals has no compatible list operation.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_LIST", "PARSE",
                    ("ibis-sqlite",), "SQLite cannot parse a string into a typed array.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_STRUCT", "CAST",
                    ("pandas", "narwhals-pandas"), "Pandas cannot preserve native struct nulls for this cast.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_CATEGORICAL", "CAST",
                    ("ibis-sqlite",), "This integer categorical cast is unsupported by SQLite.")
_intrinsic_refusals("FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL", "PARSE_GEOPOINT",
                    ("ibis-sqlite",), "SQLite cannot provide THROW for the default lexical geopoint call.")



# ── Collect test cases ────────────────────────────────────────────────────


def _collect_smoke_cases() -> list[tuple[str, str]]:
    ExpressionFunctionRegistry._init_registry()
    return [
        (str(fkey), backend)
        for fkey in ExpressionFunctionRegistry._functions
        if not is_non_expression_fkey(fkey)
        for backend in ALL_BACKENDS
    ]


_SMOKE_CASES = _collect_smoke_cases()


def _resolve_fkey(fkey_str: str) -> Enum:
    for k in ExpressionFunctionRegistry._functions:
        if str(k) == fkey_str:
            return k
    raise KeyError(f"FKEY not found: {fkey_str}")


# ── Actual smoke construction ──────────────────────────────────────────────
# Case discovery is registry-driven; each case constructs through the public API
# and runs the real compiler without consulting policy rows or catalogues.

_SMOKE_DATA = {
    "a": [1, 2, None],
    "b": [1, 1, 2],
    "c": ["hello", "world", None],
    "d": [1.0, 2.0, None],
    "e": [True, False, None],
    "f": [3, 4, None],
    "g": [5, 6, None],
    "h": [7, 8, None],
    "text": ["hello", "world", None],
    "number": [1, 2, None],
    "flag": [True, False, None],
    "date": ["2024-01-01", "2024-06-15", None],
}


def _smoke_data(fkey):
    data = dict(_SMOKE_DATA)
    category = _get_category_for_fkey(fkey)
    if category == "datetime":
        data["a"] = [datetime(2024, 1, 1), datetime(2024, 6, 15), None]
        if fkey.name.startswith("TOTAL_"):
            data["a"] = [timedelta(days=1), timedelta(days=2), None]
    elif category == "list" and fkey.name != "PARSE":
        data["a"] = [[1, 2], [3, 4], None]
        if fkey.name in {"ALL", "ANY"}:
            data["a"] = [[True, False], [True, True], None]
        elif fkey.name == "JOIN":
            data["a"] = [["a", "b"], ["c", "d"], None]
        elif fkey.name == "CAST_ITEMS":
            data["a"] = [[{"id": "1"}], [{"id": "2"}], None]
        elif fkey.name == "GATHER":
            data["b"] = [[0], [0], None]
    elif category == "struct":
        data["a"] = [{"a": 1, "id": "1"}, {"a": 2, "id": "2"}, None]
    return data


class _SmokeNotApplicable(Exception):  # noqa: N818 - control-flow signal, not an error
    def __init__(self, outcome: str, message: str) -> None:
        super().__init__(message)
        self.outcome = outcome
        self.message = message


def _prepare_smoke_case(fkey_str: str, frame: object) -> Callable[[], Any]:
    """Build one public API invocation and return its real compile callback."""
    ExpressionFunctionRegistry._init_registry()
    fkey = _resolve_fkey(fkey_str)

    fdef = ExpressionFunctionRegistry.get(fkey)
    builder = get_smoke_expr_builder(fkey)
    if builder is not _SENTINEL_MISSING:
        if builder is None:
            raise _SmokeNotApplicable("fail", f"{fkey_str}: {fdef.protocol_method.__name__} not reachable via public API (API builder stub or internal utility)")
        expr = builder()
        return lambda: expr.compile(frame)
    try:
        args, options = build_args_for_fkey(fkey, fdef)
    except ValueError as exc:
        raise _SmokeNotApplicable("fail", f"Cannot auto-construct args for {fkey_str}: {exc}. Add to _SMOKE_ARG_OVERRIDES in _smoke_helpers.py.") from exc
    method_name = fdef.protocol_method.__name__
    if not args:
        free_fn = getattr(ma, method_name, None)
        if free_fn is None:
            raise _SmokeNotApplicable(
                "fail", f"{fkey_str}: no-argument public API is missing ma.{method_name}"
            )
        try:
            expr = free_fn(**options)
        except TypeError as exc:
            raise _SmokeNotApplicable(
                "fail", f"{fkey_str}: ma.{method_name}(**{options}) raised TypeError: {exc}"
            ) from exc
        return lambda: expr.compile(frame)
    base, *remaining_args = args
    callable_method = _resolve_api_callable(base, method_name)
    if callable_method is None:
        free_fn = getattr(ma, method_name, None)
        if free_fn is not None:
            try:
                expr = free_fn(*args, **options)
            except TypeError as exc:
                raise _SmokeNotApplicable(
                    "fail",
                    f"{fkey_str}: ma.{method_name}(*args, **options) raised TypeError: {exc}",
                ) from exc
            return lambda: expr.compile(frame)
        raise _SmokeNotApplicable(
            "fail", f"{fkey_str}: {method_name} is not reachable through the public API"
        )
    try:
        expr = callable_method(*remaining_args, **options)
    except TypeError as exc:
        raise _SmokeNotApplicable("fail", f"{fkey_str}: API builder raised TypeError: {exc}") from exc
    return lambda: expr.compile(frame)


def test_smoke_discovery_covers_every_executable_registered_fkey_and_backend() -> None:
    ExpressionFunctionRegistry._init_registry()
    non_expression = {
        str(fkey)
        for fkey in ExpressionFunctionRegistry._functions
        if is_non_expression_fkey(fkey)
    }
    compiled = {fkey for fkey, _ in _SMOKE_CASES}
    registered = {str(fkey) for fkey in ExpressionFunctionRegistry._functions}
    assert non_expression == {"FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES"}
    assert compiled.isdisjoint(non_expression)
    assert compiled | non_expression == registered
    assert set(_SMOKE_CASES) == {
        (fkey, backend) for fkey in compiled for backend in ALL_BACKENDS
    }


# ── Test class ────────────────────────────────────────────────────────────


class TestCompileSmoke:
    """Compile every executable FKEY on every backend with explicit witnesses."""

    @pytest.mark.parametrize(
        ("fkey_str", "backend_name"),
        _SMOKE_CASES,
        ids=[f"{fk}/{bn}" for fk, bn in _SMOKE_CASES],
    )
    def test_compile_succeeds(
        self, fkey_str: str, backend_name: str, backend_factory
    ) -> None:
        witness = _NATIVE_SMOKE_WITNESSES.get((fkey_str, backend_name))
        data = _smoke_data(_resolve_fkey(fkey_str))
        constructor_errors = ()
        if backend_name == "ibis-sqlite":
            if isinstance(data["a"][0], (list, dict)):
                from ibis.common.exceptions import UnsupportedBackendType

                constructor_errors = (UnsupportedBackendType,)
            elif isinstance(data["a"][0], timedelta):
                from sqlite3 import ProgrammingError

                constructor_errors = (ProgrammingError,)
        with expect_call_failure(
            reason="SQLite cannot construct this native input type; expression compilation is not reached.",
            errors=constructor_errors,
            when=bool(constructor_errors),
        ):
            frame = backend_factory.create(data, backend_name)
        try:
            compile_call = _prepare_smoke_case(fkey_str, frame)
        except _SmokeNotApplicable as not_applicable:
            pytest.fail(not_applicable.message)
        try:
            compile_call()
        except Exception as exc:
            if witness is None:
                pytest.fail(
                    f"{fkey_str} on {backend_name}: compile() raised "
                    f"{type(exc).__name__}: {exc}"
                )
            if type(exc) is not witness.error_type:
                pytest.fail(
                    f"{fkey_str} on {backend_name}: expected "
                    f"{witness.error_type.__name__}, got {type(exc).__name__}: {exc}"
                )
            if witness.error_type is BackendCapabilityError:
                assert str(exc.function_key) == fkey_str, (
                    f"{fkey_str} on {backend_name}: backend refusal named "
                    f"{exc.function_key!s}, not the exercised FKEY"
                )
                assert not witness.strict_xfail
                return
            if witness.strict_xfail:
                pytest.xfail(witness.reason)
            pytest.fail(f"{fkey_str} on {backend_name}: non-xfail witness was not a refusal")
        else:
            if witness is not None:
                pytest.fail(
                    f"{fkey_str} on {backend_name}: witness says "
                    f"{witness.error_type.__name__} but compile() succeeded"
                )



# ── Meta-tests ────────────────────────────────────────────────────────────


class TestSmokeWitnessIntegrity:
    """Validate the exact local compile witnesses."""

    def test_every_witness_has_an_executed_case(self) -> None:
        assert set(_NATIVE_SMOKE_WITNESSES) <= set(_SMOKE_CASES)

