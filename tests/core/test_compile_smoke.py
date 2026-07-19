"""Compile smoke tests — every FKEY × 7 backends must compile without exception.

Introspection-driven: enumerates all FKEYs from the function registry, builds
a minimal expression via protocol signature introspection, and calls
.compile(df) on each backend. Catches wiring errors (wrong method name,
missing method, arity mismatch) but not type errors at execution time.
"""
from __future__ import annotations

import re
import sys
from enum import Enum
from pathlib import Path

import pytest

import mountainash as ma
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)

_TESTS_DIR = str(Path(__file__).resolve().parent.parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from core._smoke_helpers import (
    _SENTINEL_MISSING,
    build_args_for_fkey,
    get_smoke_expr_builder,
    is_non_expression_fkey,
    is_variadic,
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
_DESCRIPTOR_NAMESPACES = ("str", "dt", "list", "struct")


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


# ── Exception set ─────────────────────────────────────────────────────────
# (fkey_str, backend_name) → "reason. Since YYYY-MM-DD."
#
# 497 entries across 109 unique FKEYs. Failure categories:
#   276  BackendCapabilityError — backend explicitly rejects the operation
#   108  NotImplementedError — operation not wired for this backend
#    53  TypeError — arg construction mismatch (needs _SMOKE_ARG_OVERRIDES)
#    35  Window requires .over() — window functions need .over() context
#    12  AttributeError — missing method on backend
#     7  Pydantic ValidationError — API builder passes options=None
#     4  ValueError — bad default option value
#     2  Other (ComputeError, InvalidOperationError)
_KNOWN_SMOKE_FAILURES: dict[tuple[str, str], str] = {
    # ── BackendCapabilityError (276 entries) ──
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES", "pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals datetime offset operations require literal integer values Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.AGG", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.agg(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.AGG", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.agg(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.AGG", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.agg(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.AGG", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.agg(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.AGG", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.agg(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.AGG", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.agg(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ALL", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.all(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ALL", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.all(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ALL", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.all(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ANY", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.any(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ANY", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.any(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ANY", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.any(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.arg_max(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.arg_max(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.arg_max(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.arg_max(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.arg_max(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MAX", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.arg_max(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.arg_min(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.arg_min(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.arg_min(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.arg_min(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.arg_min(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ARG_MIN", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.arg_min(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.CONCAT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.concat(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.CONCAT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.concat(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.CONCAT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.concat(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.count_matches(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.count_matches(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.count_matches(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.count_matches(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.count_matches(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.count_matches(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DIFF", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.diff(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DIFF", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.diff(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DIFF", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.diff(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DIFF", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.diff(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DIFF", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.diff(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DIFF", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.diff(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.drop_nulls(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.drop_nulls(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.drop_nulls(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.drop_nulls(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.drop_nulls(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.drop_nulls(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.explode(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.explode(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.explode(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.FILTER", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis array.filter() requires a Deferred/Callable predicate, which is incompatible with... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.FILTER", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis array.filter() requires a Deferred/Callable predicate, which is incompatible with... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.FILTER", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis array.filter() requires a Deferred/Callable predicate, which is incompatible with... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.FILTER", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.filter(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.FILTER", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.filter(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.FILTER", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.filter(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.gather(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.gather(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.gather(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.gather(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.gather(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.gather(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.gather_every(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.gather_every(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.gather_every(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.gather_every(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.gather_every(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.gather_every(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.HEAD", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.head(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.HEAD", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.head(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.HEAD", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.head(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.HEAD", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.head(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.HEAD", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.head(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.HEAD", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.head(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ITEM", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.item(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ITEM", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.item(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ITEM", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.item(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ITEM", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.item(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ITEM", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.item(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.ITEM", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.item(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.JOIN", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.join(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.JOIN", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.join(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.JOIN", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.join(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.MEDIAN", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.median(). Use Polars or Narwhals backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.MEDIAN", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.median(). Use Polars or Narwhals backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.MEDIAN", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.median(). Use Polars or Narwhals backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.n_unique(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.n_unique(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.n_unique(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.n_unique(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.n_unique(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.n_unique(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.reverse(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.reverse(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.reverse(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.reverse(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.reverse(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.reverse(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.sample(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.sample(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.sample(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.sample(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.sample(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.sample(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.set_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.set_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.set_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_INTERSECTION", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_intersection(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_INTERSECTION", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_intersection(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_INTERSECTION", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_intersection(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.set_symmetric_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.set_symmetric_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.set_symmetric_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_symmetric_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_symmetric_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_symmetric_difference(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_UNION", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_union(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_UNION", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_union(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SET_UNION", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.set_union(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.shift(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.shift(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.shift(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.shift(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.shift(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.shift(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SLICE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.slice(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SLICE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.slice(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SLICE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.slice(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SLICE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.slice(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SLICE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.slice(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.SLICE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.slice(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.STD", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.std(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.STD", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.std(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.STD", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.std(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.STD", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.std(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.STD", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.std(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.STD", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.std(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TAIL", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.tail(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TAIL", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.tail(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TAIL", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.tail(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TAIL", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.tail(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TAIL", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.tail(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TAIL", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.tail(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.to_struct(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.to_struct(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.to_struct(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.to_struct(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.to_struct(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.to_struct(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.VAR", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support array.var(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.VAR", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support array.var(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.VAR", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support array.var(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.VAR", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.var(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.VAR", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support list.var(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.VAR", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support list.var(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.DECODE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support str.decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.DECODE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support str.decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.DECODE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support str.decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.DECODE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.DECODE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support str.decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.DECODE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support str.encode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support str.encode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support str.encode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.encode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support str.encode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.encode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support str.extract_groups(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support str.extract_groups(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support str.extract_groups(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.extract_groups(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support str.extract_groups(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.EXTRACT_GROUPS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.extract_groups(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support str.json_decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support str.json_decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support str.json_decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.json_decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support str.json_decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_DECODE", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.json_decode(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support str.json_path_match(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support str.json_path_match(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support str.json_path_match(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.json_path_match(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support str.json_path_match(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.JSON_PATH_MATCH", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.json_path_match(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support str.to_time(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support str.to_time(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support str.to_time(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.to_time(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support str.to_time(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.TO_TIME", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.to_time(). Use Polars backend. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis has no expression-level forward_fill/backward_fill. Use relation-level compositio... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis has no expression-level forward_fill/backward_fill. Use relation-level compositio... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis has no expression-level forward_fill/backward_fill. Use relation-level compositio... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis has no expression-level forward_fill/backward_fill. Use relation-level compositio... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis has no expression-level forward_fill/backward_fill. Use relation-level compositio... Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis has no expression-level forward_fill/backward_fill. Use relation-level compositio... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.BITWISE_XOR", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise_xor. Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.BITWISE_XOR", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise_xor. Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.BITWISE_XOR", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise_xor. Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_LEFT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise shift_left. Use Ibis backend for shift operations. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_LEFT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise shift_left. Use Ibis backend for shift operations. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_LEFT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise shift_left. Use Ibis backend for shift operations. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_LEFT", "polars"): "BackendCapabilityError: [polars] Polars does not support bitwise shift_left. Use Ibis backend for shift operations. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise shift_right. Use Ibis backend for shift operations. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise shift_right. Use Ibis backend for shift operations. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support bitwise shift_right. Use Ibis backend for shift operations. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT", "polars"): "BackendCapabilityError: [polars] Polars does not support bitwise shift_right. Use Ibis backend for shift operations. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED", "ibis-duckdb"): "BackendCapabilityError: [ibis] No backend supports bitwise shift_right_unsigned. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED", "ibis-polars"): "BackendCapabilityError: [ibis] No backend supports bitwise shift_right_unsigned. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED", "ibis-sqlite"): "BackendCapabilityError: [ibis] No backend supports bitwise shift_right_unsigned. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED", "narwhals-pandas"): "BackendCapabilityError: [narwhals] No backend supports bitwise shift_right_unsigned. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED", "narwhals-polars"): "BackendCapabilityError: [narwhals] No backend supports bitwise shift_right_unsigned. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED", "pandas"): "BackendCapabilityError: [narwhals] No backend supports bitwise shift_right_unsigned. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SHIFT_RIGHT_UNSIGNED", "polars"): "BackendCapabilityError: [polars] No backend supports bitwise shift_right_unsigned. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.LEFT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.LEFT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.LEFT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.LPAD", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.LPAD", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.LPAD", "pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support regexp_count_substring (no count_matches method). Use Polars bac... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support regexp_count_substring (no count_matches method). Use Polars bac... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support regexp_count_substring (no count_matches method). Use Polars bac... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_count_substring (no count_matches method). Use Po... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_count_substring (no count_matches method). Use Po... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_COUNT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_count_substring (no count_matches method). Use Po... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support regexp_match_substring_all (no extract_all equivalent). Use Pola... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support regexp_match_substring_all (no extract_all equivalent). Use Pola... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support regexp_match_substring_all (no extract_all equivalent). Use Pola... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_match_substring_all (no extract_all method). Use ... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_match_substring_all (no extract_all method). Use ... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_MATCH_ALL", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_match_substring_all (no extract_all method). Use ... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS", "ibis-duckdb"): "BackendCapabilityError: [ibis] Ibis does not support regexp_strpos (no regex find method). Use Polars backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS", "ibis-polars"): "BackendCapabilityError: [ibis] Ibis does not support regexp_strpos (no regex find method). Use Polars backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS", "ibis-sqlite"): "BackendCapabilityError: [ibis] Ibis does not support regexp_strpos (no regex find method). Use Polars backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_strpos (no regex find method). Use Polars backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_strpos (no regex find method). Use Polars backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_STRPOS", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support regexp_strpos (no regex find method). Use Polars backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.repeat(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals does not support str.repeat(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals does not support str.repeat(). Use Polars or Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.RIGHT", "pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.RPAD", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.RPAD", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.RPAD", "pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING", "narwhals-pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING", "narwhals-polars"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.SUBSTRING", "pandas"): "BackendCapabilityError: [narwhals] Narwhals string methods require literal values, not column references, on the pand... Since 2026-05-18.",
    # ── NotImplementedError (108 entries) ──
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
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE", "narwhals-pandas"): "NotImplementedError: mode() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE", "narwhals-polars"): "NotImplementedError: mode() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE", "pandas"): "NotImplementedError: mode() is not supported by the Narwhals backend. Since 2026-05-18.",
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
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP", "narwhals-pandas"): "NotImplementedError: exp() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP", "narwhals-polars"): "NotImplementedError: exp() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP", "pandas"): "NotImplementedError: exp() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "narwhals-pandas"): "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "narwhals-polars"): "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS", "pandas"): "NotImplementedError: radians() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN", "narwhals-pandas"): "NotImplementedError: sign() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN", "narwhals-polars"): "NotImplementedError: sign() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN", "pandas"): "NotImplementedError: sign() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "narwhals-pandas"): "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "narwhals-polars"): "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN", "pandas"): "NotImplementedError: sin() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-duckdb"): "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-polars"): "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "ibis-sqlite"): "NotImplementedError: sinh() is not directly supported by the Ibis backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "narwhals-pandas"): "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "narwhals-polars"): "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH", "pandas"): "NotImplementedError: sinh() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT", "narwhals-pandas"): "NotImplementedError: sqrt() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT", "narwhals-polars"): "NotImplementedError: sqrt() is not supported by the Narwhals backend. Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT", "pandas"): "NotImplementedError: sqrt() is not supported by the Narwhals backend. Since 2026-05-18.",
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
    # ── TypeError (arg construction) (53 entries) ──
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
    ("FKEY_SUBSTRAIT_SCALAR_STRING.CENTER", "polars"): "TypeError: int() argument must be a string, a bytes-like object or a real number, not 'Expr' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REPEAT", "polars"): "TypeError: int() argument must be a string, a bytes-like object or a real number, not 'Expr' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE_SLICE", "polars"): "TypeError: int() argument must be a string, a bytes-like object or a real number, not 'Expr' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "ibis-duckdb"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "ibis-polars"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "ibis-sqlite"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "narwhals-pandas"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "narwhals-polars"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "pandas"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.NTILE", "polars"): "API: TypeError: SubstraitWindowArithmeticAPIBuilder.ntile() missing 1 required positional argument: 'n' Since 2026-05-18.",
    # ── AttributeError (missing method) (12 entries) ──
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK", "narwhals-pandas"): "AttributeError: 'ExprDateTimeNamespace' object has no attribute 'week' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK", "narwhals-polars"): "AttributeError: 'ExprDateTimeNamespace' object has no attribute 'week' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK", "pandas"): "AttributeError: 'ExprDateTimeNamespace' object has no attribute 'week' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.VARIANCE", "narwhals-pandas"): "AttributeError: 'Expr' object has no attribute 'pow' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.VARIANCE", "narwhals-polars"): "AttributeError: 'Expr' object has no attribute 'pow' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_AGGREGATE.VARIANCE", "pandas"): "AttributeError: 'Expr' object has no attribute 'pow' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FINITE", "narwhals-pandas"): "AttributeError: 'Expr' object has no attribute 'is_infinite' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FINITE", "narwhals-polars"): "AttributeError: 'Expr' object has no attribute 'is_infinite' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FINITE", "pandas"): "AttributeError: 'Expr' object has no attribute 'is_infinite' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_INFINITE", "narwhals-pandas"): "AttributeError: 'Expr' object has no attribute 'is_infinite' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_INFINITE", "narwhals-polars"): "AttributeError: 'Expr' object has no attribute 'is_infinite' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_INFINITE", "pandas"): "AttributeError: 'Expr' object has no attribute 'is_infinite' Since 2026-05-18.",
    # ── ValueError (4 entries) ──
    ("FKEY_MOUNTAINASH_SCALAR_STRING.DECODE", "polars"): "ValueError: `encoding` must be one of {'hex', 'base64'}, got 'x' Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_STRING.ENCODE", "polars"): "ValueError: `encoding` must be one of {'hex', 'base64'}, got 'x' Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.LPAD", "polars"): "ValueError: expected a string of length 1 Since 2026-05-18.",
    ("FKEY_SUBSTRAIT_SCALAR_STRING.RPAD", "polars"): "ValueError: expected a string of length 1 Since 2026-05-18.",
    # ── Other (2 entries) ──
    ("FKEY_SUBSTRAIT_SCALAR_DATETIME.ASSUME_TIMEZONE", "polars"): "ComputeError: unable to parse time zone: 'x'. Please check the Time Zone Database for a list of available time zones. Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_LIST.TO_STRUCT", "polars"): "InvalidOperationError: `Expr.list.to_struct` requires either `fields` to be a sequence or `upper_bound` to be set. Since 2026-05-18.",

    # ── Pydantic ValidationError (7 entries) ──
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST", "polars"): "API builder passes options=None to ScalarFunctionNode (Pydantic rejects). Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST", "pandas"): "API builder passes options=None to ScalarFunctionNode (Pydantic rejects). Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST", "narwhals-polars"): "API builder passes options=None to ScalarFunctionNode (Pydantic rejects). Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST", "narwhals-pandas"): "API builder passes options=None to ScalarFunctionNode (Pydantic rejects). Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST", "ibis-polars"): "API builder passes options=None to ScalarFunctionNode (Pydantic rejects). Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST", "ibis-duckdb"): "API builder passes options=None to ScalarFunctionNode (Pydantic rejects). Since 2026-05-18.",
    ("FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST", "ibis-sqlite"): "API builder passes options=None to ScalarFunctionNode (Pydantic rejects). Since 2026-05-18.",

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
    # ── Smoke expr builder: newly-exposed backend limitations (21 entries) ──
    # TO_DATE / TO_DATETIME — Narwhals backend does not implement strptime
    ("FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE", "pandas"): "NotImplementedError: strptime_date() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE", "narwhals-polars"): "NotImplementedError: strptime_date() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE", "narwhals-pandas"): "NotImplementedError: strptime_date() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP", "pandas"): "NotImplementedError: strptime_timestamp() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP", "narwhals-polars"): "NotImplementedError: strptime_timestamp() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP", "narwhals-pandas"): "NotImplementedError: strptime_timestamp() is not supported by the Narwhals backend. Since 2026-05-20.",
    # RANK (average method) — Ibis SQL has no rank(method='average') equivalent
    ("SUBSTRAIT_ARITHMETIC_WINDOW.RANK", "ibis-polars"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='average'). Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.RANK", "ibis-duckdb"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='average'). Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.RANK", "ibis-sqlite"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='average'). Since 2026-05-20.",
    # PERCENT_RANK — Narwhals backend does not implement percent_rank()
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "pandas"): "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "narwhals-polars"): "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK", "narwhals-pandas"): "NotImplementedError: percent_rank() is not supported by the Narwhals backend. Since 2026-05-20.",
    # CUME_DIST — Narwhals backend does not implement cume_dist()
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "pandas"): "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "narwhals-polars"): "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20.",
    ("SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST", "narwhals-pandas"): "NotImplementedError: cume_dist() is not supported by the Narwhals backend. Since 2026-05-20.",
    # RANK_MAX — Ibis SQL has no rank(method='max') equivalent
    ("FKEY_MOUNTAINASH_WINDOW.RANK_MAX", "ibis-polars"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='max'). Since 2026-05-20.",
    ("FKEY_MOUNTAINASH_WINDOW.RANK_MAX", "ibis-duckdb"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='max'). Since 2026-05-20.",
    ("FKEY_MOUNTAINASH_WINDOW.RANK_MAX", "ibis-sqlite"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='max'). Since 2026-05-20.",
    # RANK_AVERAGE — Ibis SQL has no rank(method='average') equivalent
    ("FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE", "ibis-polars"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='average'). Since 2026-05-20.",
    ("FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE", "ibis-duckdb"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='average'). Since 2026-05-20.",
    ("FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE", "ibis-sqlite"): "BackendCapabilityError: Ibis has no SQL equivalent for rank(method='average'). Since 2026-05-20.",
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
            pytest.xfail(_KNOWN_SMOKE_FAILURES[key])

        ExpressionFunctionRegistry._init_registry()
        fkey = _resolve_fkey(fkey_str)
        if is_non_expression_fkey(fkey):
            data = {"a": [1, 2, 3], "b": [4, 5, 6]}
            test_df = backend_factory.create(data, backend_name)
            builder = get_smoke_expr_builder(fkey)
            if builder is not _SENTINEL_MISSING and builder is not None:
                try:
                    builder().compile(test_df)
                except Exception:
                    pass
                else:
                    pytest.fail(
                        f"{fkey_str}: was non-expression FKEY but now compiles — "
                        "remove from _SMOKE_NON_EXPRESSION_FKEYS"
                    )
            pytest.xfail(
                f"{fkey_str}: AST-internal node, not a compilable expression"
            )
        fdef = ExpressionFunctionRegistry.get(fkey)

        try:
            args, options = build_args_for_fkey(fkey, fdef)
        except ValueError as e:
            pytest.fail(
                f"Cannot auto-construct args for {fkey_str}: {e}. "
                f"Add to _SMOKE_ARG_OVERRIDES in _smoke_helpers.py."
            )

        data = {
            "a": [1, 2, 3],
            "b": [4, 5, 6],
            "c": ["x", "y", "z"],
            "d": [1.0, 2.0, 3.0],
            "e": [True, False, True],
            "f": [7, 8, 9],
            "g": [10, 11, 12],
            "h": [13, 14, 15],
        }
        df = backend_factory.create(data, backend_name)

        builder = get_smoke_expr_builder(fkey)
        if builder is not _SENTINEL_MISSING:
            if builder is None:
                method_name = fdef.protocol_method.__name__
                pytest.fail(
                    f"{fkey_str}: {method_name} not reachable via public API "
                    f"(API builder stub or internal utility)"
                )
            expr = builder()
            try:
                expr.compile(df)
            except Exception as e:
                pytest.fail(
                    f"{fkey_str} on {backend_name}: compile() raised "
                    f"{type(e).__name__}: {e}"
                )
            return

        method_name = fdef.protocol_method.__name__

        # Zero-arg FKEYs (e.g. count_records, always_true, now): try free-function
        # dispatch on the ma namespace before giving up.
        if not args:
            free_fn = getattr(ma, method_name, None)
            if free_fn is None:
                pytest.skip(f"{fkey_str}: no args and ma.{method_name} not on public API")
            try:
                expr = free_fn(**options)
            except TypeError as e:
                pytest.fail(
                    f"{fkey_str}: ma.{method_name}(**{options}) raised TypeError: {e}"
                )
            try:
                expr.compile(df)
            except Exception as e:
                pytest.fail(
                    f"{fkey_str} on {backend_name}: compile() raised "
                    f"{type(e).__name__}: {e}"
                )
            return

        base = args[0]
        remaining_args = args[1:]

        callable_method = _resolve_api_callable(base, method_name)

        # Free-function fallback: if the FKEY isn't a method on the base expression
        # or any namespace, try ma.<method_name>(*args, **options) — covers free
        # functions like ma.corr(x, y), ma.quantile(x, q), ma.coalesce(...).
        if callable_method is None:
            free_fn = getattr(ma, method_name, None)
            if free_fn is not None:
                try:
                    expr = free_fn(*args, **options)
                except TypeError as e:
                    pytest.fail(
                        f"{fkey_str}: ma.{method_name}(*args, **options) raised TypeError: {e}"
                    )
                try:
                    expr.compile(df)
                except Exception as e:
                    pytest.fail(
                        f"{fkey_str} on {backend_name}: compile() raised "
                        f"{type(e).__name__}: {e}"
                    )
                return
            pytest.skip(f"{method_name} not on public API")

        try:
            expr = callable_method(*remaining_args, **options)
        except TypeError as e:
            pytest.fail(
                f"{fkey_str} on {backend_name}: API builder raised TypeError: {e}"
            )

        try:
            expr.compile(df)
        except Exception as e:
            pytest.fail(
                f"{fkey_str} on {backend_name}: compile() raised "
                f"{type(e).__name__}: {e}"
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
