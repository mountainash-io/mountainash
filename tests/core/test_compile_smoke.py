"""Compile smoke tests — every FKEY × 7 backends must compile without exception.

Introspection-driven: enumerates all FKEYs from the function registry, builds
a minimal expression via protocol signature introspection, and calls
.compile(df) on each backend. Catches wiring errors (wrong method name,
missing method, arity mismatch) but not type errors at execution time.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import pytest

import mountainash as ma
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_nodes import (
    ExpressionNode,
    ScalarFunctionNode,
)
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)
from mountainash.expressions.core.unified_visitor.visitor import (
    _param_name_for,
    _protocol_sig_params,
)

if TYPE_CHECKING:
    from enum import Enum

_TESTS_DIR = str(Path(__file__).resolve().parent.parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from core._smoke_helpers import (  # noqa: E402
    _SENTINEL_MISSING,
    build_args_for_fkey,
    get_smoke_expr_builder,
    is_non_expression_fkey,
)
from tests.fixtures.capability_gating import (  # noqa: E402
    capability_gate,
    resolve_identity,
)
from tests.fixtures.capability_inventory import (  # noqa: E402
    inventory_has,
    load_inventory,
    regenerate_inventory,
    runtime_observable_entry,
)

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
    base: ma.Expression, method_name: str
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


# Non-capability smoke failures ONLY. Every entry here MUST describe a
# NON-BackendCapabilityError outcome (native NotImplementedError / TypeError /
# AttributeError / ValueError / Pydantic ValidationError / ComputeError / ...).
# BackendCapabilityError outcomes are NOT hardcoded here: they are adjudicated
# at the runtime channel by the closed rule in ``test_compile_succeeds`` —
# fact-backed raises assert their ``.limitation``; undeclared raises fail unless
# inventoried in the spine-derived allowlist. The integrity test
# ``test_known_smoke_failures_holds_no_capability_entries`` enforces this split.
_KNOWN_SMOKE_FAILURES: dict[tuple[str, str], str] = {
    # ── NotImplementedError (124 entries) ──
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH", "narwhals-pandas"): "NotImplementedError: Narwhals does not support days_in_month() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH", "narwhals-polars"): "NotImplementedError: Narwhals does not support days_in_month() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH", "pandas"): "NotImplementedError: Narwhals does not support days_in_month() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END", "narwhals-pandas"): "NotImplementedError: Narwhals does not support month_end() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END", "narwhals-polars"): "NotImplementedError: Narwhals does not support month_end() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END", "pandas"): "NotImplementedError: Narwhals does not support month_end() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START", "narwhals-pandas"): "NotImplementedError: Narwhals does not support month_start() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START", "narwhals-polars"): "NotImplementedError: Narwhals does not support month_start() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START", "pandas"): "NotImplementedError: Narwhals does not support month_start() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME", "narwhals-pandas"): "NotImplementedError: Narwhals does not support .dt.time() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME", "narwhals-polars"): "NotImplementedError: Narwhals does not support .dt.time() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME", "pandas"): "NotImplementedError: Narwhals does not support .dt.time() Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_DAYS", "ibis-duckdb"): "NotImplementedError: Ibis IntervalValue has no total_days() method. Use dt.diff_days() for integer-based extraction. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_DAYS", "ibis-polars"): "NotImplementedError: Ibis IntervalValue has no total_days() method. Use dt.diff_days() for integer-based extraction. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_DAYS", "ibis-sqlite"): "NotImplementedError: Ibis IntervalValue has no total_days() method. Use dt.diff_days() for integer-based extraction. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_HOURS", "ibis-duckdb"): "NotImplementedError: Ibis IntervalValue has no total_hours() method. Use dt.diff_hours() for integer-based extraction. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_HOURS", "ibis-polars"): "NotImplementedError: Ibis IntervalValue has no total_hours() method. Use dt.diff_hours() for integer-based extraction. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_HOURS", "ibis-sqlite"): "NotImplementedError: Ibis IntervalValue has no total_hours() method. Use dt.diff_hours() for integer-based extraction. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MICROSECONDS", "ibis-duckdb"): "NotImplementedError: Ibis IntervalValue has no total_microseconds() method. Use integer arithmetic on dt.diff_seconds... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MICROSECONDS", "ibis-polars"): "NotImplementedError: Ibis IntervalValue has no total_microseconds() method. Use integer arithmetic on dt.diff_seconds... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MICROSECONDS", "ibis-sqlite"): "NotImplementedError: Ibis IntervalValue has no total_microseconds() method. Use integer arithmetic on dt.diff_seconds... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MILLISECONDS", "ibis-duckdb"): "NotImplementedError: Ibis IntervalValue has no total_milliseconds() method. Use dt.diff_milliseconds() for integer-ba... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MILLISECONDS", "ibis-polars"): "NotImplementedError: Ibis IntervalValue has no total_milliseconds() method. Use dt.diff_milliseconds() for integer-ba... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MILLISECONDS", "ibis-sqlite"): "NotImplementedError: Ibis IntervalValue has no total_milliseconds() method. Use dt.diff_milliseconds() for integer-ba... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MINUTES", "ibis-duckdb"): "NotImplementedError: Ibis IntervalValue has no total_minutes() method. Use dt.diff_minutes() for integer-based extrac... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MINUTES", "ibis-polars"): "NotImplementedError: Ibis IntervalValue has no total_minutes() method. Use dt.diff_minutes() for integer-based extrac... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_MINUTES", "ibis-sqlite"): "NotImplementedError: Ibis IntervalValue has no total_minutes() method. Use dt.diff_minutes() for integer-based extrac... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_NANOSECONDS", "ibis-duckdb"): "NotImplementedError: Ibis IntervalValue has no total_nanoseconds() method. Use integer arithmetic on dt.diff_seconds(... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_NANOSECONDS", "ibis-polars"): "NotImplementedError: Ibis IntervalValue has no total_nanoseconds() method. Use integer arithmetic on dt.diff_seconds(... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_NANOSECONDS", "ibis-sqlite"): "NotImplementedError: Ibis IntervalValue has no total_nanoseconds() method. Use integer arithmetic on dt.diff_seconds(... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS", "ibis-duckdb"): "NotImplementedError: Ibis IntervalValue has no total_seconds() method. Use dt.diff_seconds() for integer-based extrac... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS", "ibis-polars"): "NotImplementedError: Ibis IntervalValue has no total_seconds() method. Use dt.diff_seconds() for integer-based extrac... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TOTAL_SECONDS", "ibis-sqlite"): "NotImplementedError: Ibis IntervalValue has no total_seconds() method. Use dt.diff_seconds() for integer-based extrac... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS", "narwhals-pandas"): "NotImplementedError: acos() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS", "narwhals-polars"): "NotImplementedError: acos() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS", "pandas"): "NotImplementedError: acos() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "ibis-duckdb"): "NotImplementedError: acosh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "ibis-polars"): "NotImplementedError: acosh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "ibis-sqlite"): "NotImplementedError: acosh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "narwhals-pandas"): "NotImplementedError: acosh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "narwhals-polars"): "NotImplementedError: acosh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH", "pandas"): "NotImplementedError: acosh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN", "narwhals-pandas"): "NotImplementedError: asin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN", "narwhals-polars"): "NotImplementedError: asin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN", "pandas"): "NotImplementedError: asin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "ibis-duckdb"): "NotImplementedError: asinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "ibis-polars"): "NotImplementedError: asinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "ibis-sqlite"): "NotImplementedError: asinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "narwhals-pandas"): "NotImplementedError: asinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "narwhals-polars"): "NotImplementedError: asinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH", "pandas"): "NotImplementedError: asinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN", "narwhals-pandas"): "NotImplementedError: atan() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN", "narwhals-polars"): "NotImplementedError: atan() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN", "pandas"): "NotImplementedError: atan() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2", "narwhals-pandas"): "NotImplementedError: atan2() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2", "narwhals-polars"): "NotImplementedError: atan2() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2", "pandas"): "NotImplementedError: atan2() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "ibis-duckdb"): "NotImplementedError: atanh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "ibis-polars"): "NotImplementedError: atanh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "ibis-sqlite"): "NotImplementedError: atanh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "narwhals-pandas"): "NotImplementedError: atanh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "narwhals-polars"): "NotImplementedError: atanh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH", "pandas"): "NotImplementedError: atanh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS", "narwhals-pandas"): "NotImplementedError: cos() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS", "narwhals-polars"): "NotImplementedError: cos() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS", "pandas"): "NotImplementedError: cos() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "ibis-duckdb"): "NotImplementedError: cosh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "ibis-polars"): "NotImplementedError: cosh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "ibis-sqlite"): "NotImplementedError: cosh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "narwhals-pandas"): "NotImplementedError: cosh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "narwhals-polars"): "NotImplementedError: cosh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH", "pandas"): "NotImplementedError: cosh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES", "narwhals-pandas"): "NotImplementedError: degrees() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES", "narwhals-polars"): "NotImplementedError: degrees() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES", "pandas"): "NotImplementedError: degrees() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "narwhals-pandas"): "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "narwhals-polars"): "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "pandas"): "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "narwhals-pandas"): "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "narwhals-polars"): "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "pandas"): "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-duckdb"): "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-polars"): "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-sqlite"): "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "narwhals-pandas"): "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "narwhals-polars"): "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "pandas"): "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN", "narwhals-pandas"): "NotImplementedError: tan() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN", "narwhals-polars"): "NotImplementedError: tan() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN", "pandas"): "NotImplementedError: tan() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "ibis-duckdb"): "NotImplementedError: tanh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "ibis-polars"): "NotImplementedError: tanh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "ibis-sqlite"): "NotImplementedError: tanh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "narwhals-pandas"): "NotImplementedError: tanh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "narwhals-polars"): "NotImplementedError: tanh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH", "pandas"): "NotImplementedError: tanh() is not supported by the Narwhals backend. Since 2026-05-18.",
    # ── Window requires .over() (35 entries) ──
    ("SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE", "ibis-duckdb"): "ValueError: Window function '7' requires .over() — e.g., col('x').first_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE", "ibis-polars"): "ValueError: Window function '7' requires .over() — e.g., col('x').first_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE", "ibis-sqlite"): "ValueError: Window function '7' requires .over() — e.g., col('x').first_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE", "narwhals-pandas"): "ValueError: Window function '7' requires .over() — e.g., col('x').first_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE", "narwhals-polars"): "ValueError: Window function '7' requires .over() — e.g., col('x').first_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE", "pandas"): "ValueError: Window function '7' requires .over() — e.g., col('x').first_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE", "polars"): "ValueError: Window function '7' requires .over() — e.g., col('x').first_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAG", "ibis-duckdb"): "ValueError: Window function '11' requires .over() — e.g., col('x').lag().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAG", "ibis-polars"): "ValueError: Window function '11' requires .over() — e.g., col('x').lag().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAG", "ibis-sqlite"): "ValueError: Window function '11' requires .over() — e.g., col('x').lag().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAG", "narwhals-pandas"): "ValueError: Window function '11' requires .over() — e.g., col('x').lag().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAG", "narwhals-polars"): "ValueError: Window function '11' requires .over() — e.g., col('x').lag().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAG", "pandas"): "ValueError: Window function '11' requires .over() — e.g., col('x').lag().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAG", "polars"): "ValueError: Window function '11' requires .over() — e.g., col('x').lag().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE", "ibis-duckdb"): "ValueError: Window function '8' requires .over() — e.g., col('x').last_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE", "ibis-polars"): "ValueError: Window function '8' requires .over() — e.g., col('x').last_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE", "ibis-sqlite"): "ValueError: Window function '8' requires .over() — e.g., col('x').last_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE", "narwhals-pandas"): "ValueError: Window function '8' requires .over() — e.g., col('x').last_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE", "narwhals-polars"): "ValueError: Window function '8' requires .over() — e.g., col('x').last_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE", "pandas"): "ValueError: Window function '8' requires .over() — e.g., col('x').last_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE", "polars"): "ValueError: Window function '8' requires .over() — e.g., col('x').last_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LEAD", "ibis-duckdb"): "ValueError: Window function '10' requires .over() — e.g., col('x').lead().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LEAD", "ibis-polars"): "ValueError: Window function '10' requires .over() — e.g., col('x').lead().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LEAD", "ibis-sqlite"): "ValueError: Window function '10' requires .over() — e.g., col('x').lead().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LEAD", "narwhals-pandas"): "ValueError: Window function '10' requires .over() — e.g., col('x').lead().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LEAD", "narwhals-polars"): "ValueError: Window function '10' requires .over() — e.g., col('x').lead().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LEAD", "pandas"): "ValueError: Window function '10' requires .over() — e.g., col('x').lead().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.LEAD", "polars"): "ValueError: Window function '10' requires .over() — e.g., col('x').lead().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE", "ibis-duckdb"): "ValueError: Window function '9' requires .over() — e.g., col('x').nth_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE", "ibis-polars"): "ValueError: Window function '9' requires .over() — e.g., col('x').nth_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE", "ibis-sqlite"): "ValueError: Window function '9' requires .over() — e.g., col('x').nth_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE", "narwhals-pandas"): "ValueError: Window function '9' requires .over() — e.g., col('x').nth_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE", "narwhals-polars"): "ValueError: Window function '9' requires .over() — e.g., col('x').nth_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE", "pandas"): "ValueError: Window function '9' requires .over() — e.g., col('x').nth_value().over('group') Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE", "polars"): "ValueError: Window function '9' requires .over() — e.g., col('x').nth_value().over('group') Since 2026-05-18.",
    # ── TypeError (arg construction) (60 entries) ──
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY", "ibis-duckdb"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.offset_by() missing 1 required positional argument: 'offset' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY", "ibis-polars"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.offset_by() missing 1 required positional argument: 'offset' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY", "ibis-sqlite"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.offset_by() missing 1 required positional argument: 'offset' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY", "narwhals-pandas"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.offset_by() missing 1 required positional argument: 'offset' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY", "narwhals-polars"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.offset_by() missing 1 required positional argument: 'offset' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY", "pandas"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.offset_by() missing 1 required positional argument: 'offset' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY", "polars"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.offset_by() missing 1 required positional argument: 'offset' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE", "ibis-duckdb"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.truncate() missing 1 required positional argument: 'unit' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE", "ibis-polars"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.truncate() missing 1 required positional argument: 'unit' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE", "ibis-sqlite"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.truncate() missing 1 required positional argument: 'unit' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE", "narwhals-pandas"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.truncate() missing 1 required positional argument: 'unit' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE", "narwhals-polars"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.truncate() missing 1 required positional argument: 'unit' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE", "pandas"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.truncate() missing 1 required positional argument: 'unit' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE", "polars"): "API: TypeError: MountainAshScalarDatetimeAPIBuilder.truncate() missing 1 required positional argument: 'unit' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GET", "ibis-duckdb"): "API: TypeError: MountainAshScalarListAPIBuilder.get() missing 1 required positional argument: 'index' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GET", "ibis-polars"): "API: TypeError: MountainAshScalarListAPIBuilder.get() missing 1 required positional argument: 'index' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GET", "ibis-sqlite"): "API: TypeError: MountainAshScalarListAPIBuilder.get() missing 1 required positional argument: 'index' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GET", "narwhals-pandas"): "API: TypeError: MountainAshScalarListAPIBuilder.get() missing 1 required positional argument: 'index' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GET", "narwhals-polars"): "API: TypeError: MountainAshScalarListAPIBuilder.get() missing 1 required positional argument: 'index' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GET", "pandas"): "API: TypeError: MountainAshScalarListAPIBuilder.get() missing 1 required positional argument: 'index' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GET", "polars"): "API: TypeError: MountainAshScalarListAPIBuilder.get() missing 1 required positional argument: 'index' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY", "ibis-duckdb"): "API: TypeError: MountainAshScalarListAPIBuilder.to_array() missing 1 required keyword-only argument: 'width' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY", "ibis-polars"): "API: TypeError: MountainAshScalarListAPIBuilder.to_array() missing 1 required keyword-only argument: 'width' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY", "ibis-sqlite"): "API: TypeError: MountainAshScalarListAPIBuilder.to_array() missing 1 required keyword-only argument: 'width' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY", "narwhals-pandas"): "API: TypeError: MountainAshScalarListAPIBuilder.to_array() missing 1 required keyword-only argument: 'width' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY", "narwhals-polars"): "API: TypeError: MountainAshScalarListAPIBuilder.to_array() missing 1 required keyword-only argument: 'width' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY", "pandas"): "API: TypeError: MountainAshScalarListAPIBuilder.to_array() missing 1 required keyword-only argument: 'width' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_ARRAY", "polars"): "API: TypeError: MountainAshScalarListAPIBuilder.to_array() missing 1 required keyword-only argument: 'width' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE", "polars"): "TypeError: `Expr.str.json_decode` needs an explicitly given `dtype` otherwise Polars is not able to determine the out... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD", "ibis-duckdb"): "API: TypeError: MountainAshScalarStructAPIBuilder.field() missing 1 required positional argument: 'name' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD", "ibis-polars"): "API: TypeError: MountainAshScalarStructAPIBuilder.field() missing 1 required positional argument: 'name' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD", "ibis-sqlite"): "API: TypeError: MountainAshScalarStructAPIBuilder.field() missing 1 required positional argument: 'name' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD", "narwhals-pandas"): "API: TypeError: MountainAshScalarStructAPIBuilder.field() missing 1 required positional argument: 'name' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD", "narwhals-polars"): "API: TypeError: MountainAshScalarStructAPIBuilder.field() missing 1 required positional argument: 'name' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD", "pandas"): "API: TypeError: MountainAshScalarStructAPIBuilder.field() missing 1 required positional argument: 'name' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD", "polars"): "API: TypeError: MountainAshScalarStructAPIBuilder.field() missing 1 required positional argument: 'name' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN", "ibis-duckdb"): "API: TypeError: MountainAshScalarListAPIBuilder.median() takes 1 positional argument but 2 were given Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN", "ibis-polars"): "API: TypeError: MountainAshScalarListAPIBuilder.median() takes 1 positional argument but 2 were given Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN", "ibis-sqlite"): "API: TypeError: MountainAshScalarListAPIBuilder.median() takes 1 positional argument but 2 were given Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN", "narwhals-pandas"): "API: TypeError: MountainAshScalarListAPIBuilder.median() takes 1 positional argument but 2 were given Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN", "narwhals-polars"): "API: TypeError: MountainAshScalarListAPIBuilder.median() takes 1 positional argument but 2 were given Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN", "pandas"): "API: TypeError: MountainAshScalarListAPIBuilder.median() takes 1 positional argument but 2 were given Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MEDIAN", "polars"): "API: TypeError: MountainAshScalarListAPIBuilder.median() takes 1 positional argument but 2 were given Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "ibis-duckdb"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "ibis-polars"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "ibis-sqlite"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "narwhals-pandas"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "narwhals-polars"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "pandas"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "polars"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    # ── AttributeError (missing method) (12 entries) ──
    # ── ValueError (4 entries) ──
    ("FKEY_MOUNTAINASH_SCALAR_STRING.DECODE", "polars"): "ValueError: `encoding` must be one of {'hex', 'base64'}, got 'x' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE", "polars"): "ValueError: `encoding` must be one of {'hex', 'base64'}, got 'x' Since 2026-05-18.",
    # ── Other (1 entry) ──
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT", "polars"): "InvalidOperationError: `Expr.list.to_struct` requires either `fields` to be a sequence or `upper_bound` to be set. Since 2026-05-18.",

    # ── Pydantic ValidationError (7 entries) ──

    # ── Newly surfaced after the free-function dispatch fallback was added
    # to the smoke runner (2026-05-20). These were previously hidden behind
    # "not on public API" skips because the helper only tried base-method
    # dispatch. See cross-backend-matrix-followups.md "Smoke helper" cluster.
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR", "polars"): "NotImplementedError: corr() requires struct context in Polars; use DataFrame.corr() instead. Tracked in cross-backend-result-verification-deferred.md. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR", "pandas"): "NotImplementedError: corr() requires struct/aggregation context. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR", "narwhals-polars"): "NotImplementedError: corr() requires struct/aggregation context. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.CORR", "narwhals-pandas"): "NotImplementedError: corr() requires struct/aggregation context. Since 2026-05-20.",
    # QUANTILE: helper's free-function dispatch passes too many positional
    # args (5) — protocol method is variadic over columns, but ma.quantile
    # takes 2 positional args (x, q). Helper needs override; for now,
    # record as known smoke failure pending arg-builder enhancement.
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE", "polars"): "TypeError: helper passes variadic columns to ma.quantile(x, q); needs arg-override. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE", "pandas"): "TypeError: helper passes variadic columns to ma.quantile(x, q); needs arg-override. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE", "narwhals-polars"): "TypeError: helper passes variadic columns to ma.quantile(x, q); needs arg-override. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE", "narwhals-pandas"): "TypeError: helper passes variadic columns to ma.quantile(x, q); needs arg-override. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE", "ibis-polars"): "TypeError: helper passes variadic columns to ma.quantile(x, q); needs arg-override. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE", "ibis-duckdb"): "TypeError: helper passes variadic columns to ma.quantile(x, q); needs arg-override. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.QUANTILE", "ibis-sqlite"): "TypeError: helper passes variadic columns to ma.quantile(x, q); needs arg-override. Since 2026-05-20.",
    # ── Smoke expr builder: newly-exposed backend limitations ──
    # PERCENT_RANK — Narwhals backend does not implement percent_rank()
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "pandas"): "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "narwhals-polars"): "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "narwhals-pandas"): "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20.",
    # CUME_DIST — Narwhals backend does not implement cume_dist()
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "pandas"): "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "narwhals-polars"): "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "narwhals-pandas"): "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20.",
}


# ── Collect test cases ────────────────────────────────────────────────────


def _collect_smoke_cases() -> list[tuple[str, str]]:
    ExpressionFunctionRegistry._init_registry()
    cases = []
    for fkey in ExpressionFunctionRegistry._functions:
        fk_str = str(fkey)
        for backend in ALL_BACKENDS:
            cases.append((fk_str, backend))
    return cases


_SMOKE_CASES = _collect_smoke_cases()


def _resolve_fkey(fkey_str: str) -> Enum:
    for k in ExpressionFunctionRegistry._functions:
        if str(k) == fkey_str:
            return k
    raise KeyError(f"FKEY not found: {fkey_str}")


# ── Spine-derived closed-rule seam ─────────────────────────────────────────
#
# The runtime channel is closed by default: a BackendCapabilityError raised by
# compile() is only acceptable when either (a) the spine declares an UNSUPPORTED
# gate fact for the invocation's precise selector — asserted as ``.limitation``
# — or (b) it sits in the runtime-observable allowlist (pending SP2). Every
# other raise fails loudly. ``_prepare_smoke_case`` is the single construction
# seam: it builds the compile callback AND carries the canonical node id plus
# the PRECISE selector (param/option_value) the invocation constructs, so the
# caller never has to re-derive a selector from a bare compile callable.

_SMOKE_DATA = {
    "a": [1, 2, 3],
    "b": [4, 5, 6],
    "c": ["x", "y", "z"],
    "d": [1.0, 2.0, 3.0],
    "e": [True, False, True],
    "f": [7, 8, 9],
    "g": [10, 11, 12],
    "h": [13, 14, 15],
}

# Canonical identity for every runtime-observable compile_smoke row. The op and
# backend live in their own identity slots, so the node id is a stable per-test
# constant (no line number to churn on every edit).
_SMOKE_NODE_ID = (
    "tests/core/test_compile_smoke.py::TestCompileSmoke::test_compile_succeeds"
)
_SMOKE_DISPLAY_SITE = "tests/core/test_compile_smoke.py:TestCompileSmoke.test_compile_succeeds"


@dataclass(frozen=True)
class PreparedSmokeCase:
    """The build/compile callback plus the identity the closed rule needs."""

    compile: Callable[[], Any]
    node_id: str
    param: str
    option_value: str | None
    gate_fact: CapabilityFact | None

class _SmokeNotApplicable(Exception):  # noqa: N818 - control-flow signal, not an error
    """Signals a construction-time skip/xfail/fail decision made BEFORE any
    compile() can run (AST-internal node, arg-construction failure, method not
    on the public API). ``outcome`` is the pytest outcome name to raise."""

    def __init__(self, outcome: str, message: str) -> None:
        super().__init__(message)
        self.outcome = outcome
        self.message = message


def _root_node(expr: object) -> object | None:
    return getattr(expr, "_node", None) or getattr(expr, "node", None)


def _fkey_scalar_node(
    node: object, fkey: Enum, seen: set[int] | None = None
) -> object | None:
    """The ScalarFunctionNode in ``expr``'s tree whose function_key is ``fkey``
    — the node the visitor gates when it compiles this invocation."""
    if seen is None:
        seen = set()
    if node is None or id(node) in seen:
        return None
    seen.add(id(node))
    if isinstance(node, ScalarFunctionNode) and node.function_key == fkey:
        return node
    for attr in ("arguments", "args"):
        for child in getattr(node, attr, None) or []:
            found = _fkey_scalar_node(child, fkey, seen)
            if found is not None:
                return found
    return None


def _derive_smoke_selector(
    fkey: Enum, fdef: object, family, dialect, expr: object
) -> tuple[str, str | None, CapabilityFact | None]:
    """Replay the production gate order and retain the selected gate fact."""
    node = _fkey_scalar_node(_root_node(expr), fkey)
    if node is None:
        return (WILDCARD_PARAM, None, None)

    op_fact = CapabilityRegistry.capability_for(fkey, WILDCARD_PARAM, family, dialect)
    if (
        op_fact is not None
        and op_fact.enforcement is Enforcement.GATE
        and op_fact.level is CapabilityLevel.UNSUPPORTED
    ):
        return (WILDCARD_PARAM, None, op_fact)

    protocol_method = getattr(fdef, "protocol_method", None)
    if protocol_method is not None:
        from mountainash.core.capabilities.predicates import bind_expression_call

        bound_call = bind_expression_call(
            operation_key=fkey,
            backend=family,
            dialect=dialect,
            protocol_method=protocol_method,
            arguments=getattr(node, "arguments", None) or [],
            options=getattr(node, "options", None) or {},
        )
        violations = CapabilityRegistry.violations_for(bound_call)
        if violations:
            fact = min(violations, key=lambda candidate: candidate.fact_key)
            value = (getattr(node, "options", None) or {}).get(fact.param)
            return (
                fact.param,
                None if isinstance(value, ExpressionNode) else str(value),
                fact,
            )

    sig = _protocol_sig_params(protocol_method) if protocol_method is not None else ()
    arguments = getattr(node, "arguments", None) or []
    for i, arg in enumerate(arguments):
        param_name = _param_name_for(sig, i)
        if param_name is None:
            continue
        fact = CapabilityRegistry.capability_for(fkey, param_name, family, dialect)
        if fact is None or fact.enforcement is not Enforcement.GATE:
            continue
        if fact.level is CapabilityLevel.UNSUPPORTED:
            return (param_name, None, fact)
        if fact.level is CapabilityLevel.LITERAL_ONLY and isinstance(arg, ExpressionNode):
            return (param_name, None, fact)

    for name, value in (getattr(node, "options", None) or {}).items():
        fact = CapabilityRegistry.capability_for(
            fkey, name, family, dialect, option_value=str(value)
        )
        if fact is None or fact.enforcement is not Enforcement.GATE:
            continue
        if fact.level is CapabilityLevel.UNSUPPORTED or (
            fact.level is CapabilityLevel.LITERAL_ONLY
            and isinstance(value, ExpressionNode)
        ):
            return (name, str(value), fact)

    return (WILDCARD_PARAM, None, None)


def test_selector_carries_the_full_compound_predicate_fact() -> None:
    from mountainash.core.capabilities.predicates import bind_expression_call
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
    )

    fkey = FK_GEO.PARSE_GEOPOINT
    expr = ma.col("c").geo.parse_geopoint(
        format="array",
        source_representation="lexical",
        field_name="c",
    )
    fdef = ExpressionFunctionRegistry.get(fkey)
    node = expr.node
    bound = bind_expression_call(
        operation_key=fkey,
        backend=CONST_BACKEND.NARWHALS,
        dialect="narwhals-polars",
        protocol_method=fdef.protocol_method,
        arguments=node.arguments,
        options=node.options,
    )
    [expected] = list(CapabilityRegistry.violations_for(bound))

    selector = _derive_smoke_selector(
        fkey,
        fdef,
        CONST_BACKEND.NARWHALS,
        "narwhals-polars",
        expr,
    )
    assert selector[:2] == ("format", "array")
    assert selector[2] is expected


def _prepare_smoke_case(fkey_str: str, frame: object) -> PreparedSmokeCase:
    """Build the invocation for ``fkey_str`` against ``frame`` and return its
    compile callback plus canonical id and precise selector. Raises
    :class:`_SmokeNotApplicable` for construction-time skip/xfail/fail cases
    that never reach a compile() call."""
    ExpressionFunctionRegistry._init_registry()
    fkey = _resolve_fkey(fkey_str)

    if is_non_expression_fkey(fkey):
        builder = get_smoke_expr_builder(fkey)
        if builder is not _SENTINEL_MISSING and builder is not None:
            try:
                builder().compile(frame)
            except Exception:
                pass
            else:
                raise _SmokeNotApplicable(
                    "fail",
                    f"{fkey_str}: was non-expression FKEY but now compiles — "
                    "remove from _SMOKE_NON_EXPRESSION_FKEYS",
                )
        raise _SmokeNotApplicable(
            "xfail", f"{fkey_str}: AST-internal node, not a compilable expression"
        )

    fdef = ExpressionFunctionRegistry.get(fkey)
    idn = resolve_identity(frame)

    def _prepared(expr: object) -> PreparedSmokeCase:
        param, option_value, gate_fact = _derive_smoke_selector(
            fkey, fdef, idn.family, idn.dialect, expr
        )
        return PreparedSmokeCase(
            compile=lambda: expr.compile(frame),
            node_id=_SMOKE_NODE_ID,
            param=param,
            option_value=option_value,
            gate_fact=gate_fact,
        )

    builder = get_smoke_expr_builder(fkey)
    if builder is not _SENTINEL_MISSING:
        if builder is None:
            method_name = fdef.protocol_method.__name__
            raise _SmokeNotApplicable(
                "fail",
                f"{fkey_str}: {method_name} not reachable via public API "
                "(API builder stub or internal utility)",
            )
        return _prepared(builder())

    try:
        args, options = build_args_for_fkey(fkey, fdef)
    except ValueError as e:
        raise _SmokeNotApplicable(
            "fail",
            f"Cannot auto-construct args for {fkey_str}: {e}. "
            "Add to _SMOKE_ARG_OVERRIDES in _smoke_helpers.py.",
        )

    method_name = fdef.protocol_method.__name__

    if not args:
        free_fn = getattr(ma, method_name, None)
        if free_fn is None:
            raise _SmokeNotApplicable(
                "skip", f"{fkey_str}: no args and ma.{method_name} not on public API"
            )
        try:
            expr = free_fn(**options)
        except TypeError as e:
            raise _SmokeNotApplicable(
                "fail", f"{fkey_str}: ma.{method_name}(**{options}) raised TypeError: {e}"
            )
        return _prepared(expr)

    base = args[0]
    remaining_args = args[1:]
    callable_method = _resolve_api_callable(base, method_name)
    if callable_method is None:
        free_fn = getattr(ma, method_name, None)
        if free_fn is not None:
            try:
                expr = free_fn(*args, **options)
            except TypeError as e:
                raise _SmokeNotApplicable(
                    "fail",
                    f"{fkey_str}: ma.{method_name}(*args, **options) raised TypeError: {e}",
                )
            return _prepared(expr)
        raise _SmokeNotApplicable("skip", f"{method_name} not on public API")

    try:
        expr = callable_method(*remaining_args, **options)
    except TypeError as e:
        raise _SmokeNotApplicable(
            "fail", f"{fkey_str}: API builder raised TypeError: {e}"
        )
    return _prepared(expr)


@lru_cache(maxsize=1)
def _smoke_inventory():
    """Parse the committed inventory once for the whole session — the closed
    rule consults it on every raise AND every non-raise (stale detection)."""
    return load_inventory()


def _iter_runtime_inventory_rows() -> list:
    """Every compile_smoke ``(fkey, backend)`` whose live BackendCapabilityError
    carries no UNSUPPORTED gate fact — the runtime-observable allowlist rows.
    Used by :func:`regenerate_smoke_inventory`; imports the factory directly so
    it runs outside a pytest fixture."""
    from tests.fixtures.backend_helpers import BackendDataFrameFactory

    ExpressionFunctionRegistry._init_registry()
    rows: list = []
    seen: set[tuple] = set()
    for fkey_str, backend_name in _collect_smoke_cases():
        if (fkey_str, backend_name) in _KNOWN_SMOKE_FAILURES:
            continue
        try:
            frame = BackendDataFrameFactory.create(_SMOKE_DATA, backend_name)
        except Exception as e:
            # A backend that cannot construct its smoke frame (missing/broken
            # library) would silently drop EVERY runtime-observable row for that
            # backend while still writing the YAML — corrupting the drain-safe
            # regeneration (spec 2.2, plan Task 0.3). Refuse loudly instead.
            raise RuntimeError(
                f"regenerate_smoke_inventory: backend {backend_name!r} failed to "
                f"construct a smoke frame ({type(e).__name__}: {e}). A full-backend "
                f"environment (all 7 backends importable) is required to regenerate "
                f"the inventory; refusing to emit a YAML with silently-dropped rows."
            ) from e
        try:
            case = _prepare_smoke_case(fkey_str, frame)
        except _SmokeNotApplicable:
            continue
        except Exception:
            continue
        fkey = _resolve_fkey(fkey_str)
        idn = resolve_identity(frame)
        fact = case.gate_fact or capability_gate(
            fkey,
            idn.family,
            dialect=idn.dialect,
            param=case.param,
            option_value=case.option_value,
        )
        try:
            case.compile()
        except BackendCapabilityError:
            if fact is not None:
                continue  # UNSUPPORTED-declared -> asserted, not allowlisted
            key = (case.node_id, fkey_str, backend_name, case.param, case.option_value)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                runtime_observable_entry(
                    node_id=case.node_id,
                    operation_key=fkey_str,
                    backend=backend_name,
                    param=case.param,
                    option_value=case.option_value,
                    current_reason=(
                        "runtime-observed BackendCapabilityError with no UNSUPPORTED "
                        "gate fact; catalogued for SP2 classification"
                    ),
                    display_site=_SMOKE_DISPLAY_SITE,
                )
            )
        except Exception:
            continue
    return rows


def regenerate_smoke_inventory(path=None):
    """Rewrite the inventory YAML with BOTH the static census rows and this
    harness's runtime-observed compile_smoke allowlist. Run this after a change
    that alters which invocations raise an undeclared BackendCapabilityError (the
    closed rule fails such a raise until it is catalogued).

    The canonical drain-safe regeneration entry point (spec 2.2): it re-observes
    the runtime rows AND re-keys every static row from the live post-edit census
    in one pass. MUST run in a full-backend env — a missing backend now raises
    (see :func:`_iter_runtime_inventory_rows`) rather than dropping rows silently.
    ``path`` (default: the committed inventory) lets a preflight regenerate into a
    temp file and compare, guarding every integration without clobbering the tree."""
    return regenerate_inventory(path=path, runtime_rows=_iter_runtime_inventory_rows())


# ── Test class ────────────────────────────────────────────────────────────


class TestCompileSmoke:
    """Every registered FKEY must compile without exception on every backend."""

    @pytest.mark.parametrize(
        ("fkey_str", "backend_name"),
        _SMOKE_CASES,
        ids=[f"{fk}/{bn}" for fk, bn in _SMOKE_CASES],
    )
    def test_compile_succeeds(
        self, fkey_str: str, backend_name: str, backend_factory
    ) -> None:
        key = (fkey_str, backend_name)
        if key in _KNOWN_SMOKE_FAILURES:
            # Machine-verify the parked reason instead of an unconditional early
            # xfail: run the real compile path and require it to still fail with a
            # NON-capability native error. A now-succeeding compile (op wired) or a
            # BackendCapabilityError (capability gap) reddens so the stale/misfiled
            # entry is surfaced rather than silently absorbed.
            expected_reason = _KNOWN_SMOKE_FAILURES[key]
            frame = backend_factory.create(_SMOKE_DATA, backend_name)
            try:
                _prepare_smoke_case(fkey_str, frame).compile()
            except BackendCapabilityError:
                pytest.fail(
                    f"{fkey_str} on {backend_name}: _KNOWN_SMOKE_FAILURES entry raised "
                    "BackendCapabilityError — capability gaps belong in the spine, not "
                    "this non-capability park"
                )
            except Exception:
                # Any non-capability failure (native compile error OR a
                # _SmokeNotApplicable construction-time signal) means the parked
                # reason still holds — xfail. Only a clean compile below is stale.
                pytest.xfail(expected_reason)
            else:
                pytest.fail(
                    f"{fkey_str} on {backend_name}: _KNOWN_SMOKE_FAILURES says "
                    f"{expected_reason!r} but compile() succeeded — remove the stale entry"
                )

        frame = backend_factory.create(_SMOKE_DATA, backend_name)
        try:
            case = _prepare_smoke_case(fkey_str, frame)
        except _SmokeNotApplicable as na:
            getattr(pytest, na.outcome)(na.message)

        fkey = _resolve_fkey(fkey_str)
        idn = resolve_identity(frame)  # object-derived (pandas routes via narwhals)
        fact = case.gate_fact or capability_gate(
            fkey,
            idn.family,
            dialect=idn.dialect,
            param=case.param,
            option_value=case.option_value,
        )
        # compile() observes ONLY the BUILD boundary; a MATERIALIZE_RESIDUE fact
        # raises at materialize, not here, so it must never drive the
        # compile()-raises expectation (nor the no-raise pytest.fail below).
        if fact is not None and fact.boundary is not Boundary.BUILD:
            fact = None
        inv = _smoke_inventory()
        try:
            case.compile()
        except BackendCapabilityError as exc:
            if fact is not None:
                assert exc.limitation is fact, (
                    f"{fkey_str} on {backend_name}: expected .limitation to be "
                    f"the BUILD gate fact {fact!r}, got {exc.limitation!r}"
                )
                return
            if inventory_has(
                case.node_id, fkey_str, backend_name,
                case.param, case.option_value, inventory=inv,
            ):
                pytest.xfail(
                    f"undeclared gap (inventoried, pending SP2): "
                    f"{fkey_str} on {backend_name}"
                )
            pytest.fail(
                f"undeclared BackendCapabilityError for {fkey_str} on "
                f"{backend_name}: no fact, not inventoried"
            )
        except Exception as e:  # non-capability compile failure — fail loudly
            pytest.fail(
                f"{fkey_str} on {backend_name}: compile() raised "
                f"{type(e).__name__}: {e}"
            )
        else:
            if fact is not None:
                pytest.fail(
                    f"{fkey_str} on {backend_name} declared UNSUPPORTED but did "
                    "not raise (upstream fixed?)"
                )
            if inventory_has(
                case.node_id, fkey_str, backend_name,
                case.param, case.option_value, inventory=inv,
            ):
                pytest.fail(
                    f"stale inventory row: {fkey_str} on {backend_name} no longer "
                    "raises — remove it"
                )


# ── Meta-tests ────────────────────────────────────────────────────────────


class TestSmokeExceptionSetIntegrity:
    """Validate the exception set format and freshness."""

    def test_every_entry_has_reason_and_date(self) -> None:
        for key, reason in _KNOWN_SMOKE_FAILURES.items():
            assert "since" in reason.lower(), (
                f"_KNOWN_SMOKE_FAILURES[{key}] missing date: {reason!r}"
            )
            assert re.search(r"\d{4}-\d{2}-\d{2}", reason), (
                f"_KNOWN_SMOKE_FAILURES[{key}] no date found: {reason!r}"
            )

    def test_every_entry_resolves_to_real_fkey_and_backend(self) -> None:
        ExpressionFunctionRegistry._init_registry()
        valid_fkeys = {str(k) for k in ExpressionFunctionRegistry._functions}
        valid_backends = set(ALL_BACKENDS)
        for fk_str, bn in _KNOWN_SMOKE_FAILURES:
            assert fk_str in valid_fkeys, (
                f"_KNOWN_SMOKE_FAILURES: FKEY {fk_str!r} not in registry"
            )
            assert bn in valid_backends, (
                f"_KNOWN_SMOKE_FAILURES: backend {bn!r} not valid"
            )

    def test_known_smoke_failures_holds_no_capability_entries(self) -> None:
        for key, reason in _KNOWN_SMOKE_FAILURES.items():
            assert "BackendCapabilityError" not in reason, (
                f"{key}: capability failures must derive from the spine, not sit "
                "in _KNOWN_SMOKE_FAILURES"
            )
