"""Relation collect smoke tests — every operation × 7 backends must collect.

Introspection-driven: enumerates relation operations from Substrait node types
and ExtensionRelOperation enum members, builds a minimal relation chain via
the public API, and calls .collect() on each backend. Catches wiring errors
(missing method, arity mismatch, visitor dispatch failure) but not result
correctness.
"""
from __future__ import annotations

import re
from typing import Any, Callable

import pytest

import mountainash as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

# ── Default test data ────────────────────────────────────────────────────

_DEFAULT_DATA = {
    "a": [1, 2, 3],
    "b": [4, 5, 6],
    "c": ["x", "y", "z"],
    "d": [1.0, 2.0, 3.0],
    "e": [True, False, True],
}

_RIGHT_DATA = {
    "a": [1, 2, 3],
    "f": [10, 20, 30],
}

# ── Fixture overrides for operations needing special data ────────────────

_SMOKE_FIXTURE_OVERRIDES: dict[str, dict[str, Any]] = {
    "explode": {
        "data": {"a": [1, 2, 3], "list_col": [[1, 2], [3, 4], [5, 6]]},
    },
    "unnest": {
        "data": {"a": [1, 2, 3], "struct_col": [{"x": 10}, {"x": 20}, {"x": 30}]},
    },
    # unpivot: keep only numeric 'b' column so all backends can melt cleanly
    "unpivot": {
        "data": {"a": [1, 2, 3], "b": [4, 5, 6], "c_num": [7, 8, 9]},
    },
    # pivot: need a column with repeated groups for index, a value col, and
    # a small pivot column so the result isn't huge
    "pivot": {
        "data": {
            "a": [1, 1, 2, 2],
            "c": ["x", "y", "x", "y"],
            "b": [10, 20, 30, 40],
        },
    },
}

# ── Operation builders ───────────────────────────────────────────────────


def _build_read(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).collect()


def _build_filter(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).filter(ma.col("a").gt(1)).collect()


def _build_select(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).select("a", "b").collect()


def _build_with_columns(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).with_columns(
        ma.col("a").add(1).name.alias("x")
    ).collect()


def _build_drop(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).drop("c").collect()


def _build_rename(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).rename({"a": "x"}).collect()


def _build_sort(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).sort("a").collect()


def _build_head(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).head(2).collect()


def _build_tail(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).tail(2).collect()


def _build_slice(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).slice(0, 2).collect()


def _build_join_inner(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).join(ma.relation(df_right), on="a").collect()


def _build_join_left(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).join(
        ma.relation(df_right), on="a", how="left"
    ).collect()


def _build_join_asof(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).join_asof(ma.relation(df_right), on="a").collect()


def _build_aggregate(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).group_by("c").agg(
        ma.col("a").sum()
    ).collect()


def _build_unique(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).unique("c").collect()


def _build_concat(df: Any, df_right: Any, **kw: Any) -> Any:
    r1 = ma.relation(df).select("a")
    r2 = ma.relation(df).select("a")
    return ma.concat([r1, r2]).collect()


def _build_drop_nulls(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).drop_nulls().collect()


def _build_drop_nans(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).drop_nans().collect()


def _build_with_row_index(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).with_row_index(name="idx").collect()


def _build_explode(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).explode("list_col").collect()


def _build_sample(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).sample(n=2).collect()


def _build_unpivot(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).unpivot(on=["b", "c_num"]).collect()


def _build_pivot(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).pivot(on="c", index="a", values="b").collect()


def _build_top_k(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).top_k(2, by="a").collect()


def _build_unnest(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation(df).unnest("struct_col", separator="_").collect()


def _build_source(df: Any, df_right: Any, **kw: Any) -> Any:
    return ma.relation([{"a": 1, "b": 2}, {"a": 3, "b": 4}]).collect()


# ── Operation registry ───────────────────────────────────────────────────

_OPERATIONS: dict[str, Callable[..., Any]] = {
    "read": _build_read,
    "filter": _build_filter,
    "select": _build_select,
    "with_columns": _build_with_columns,
    "drop": _build_drop,
    "rename": _build_rename,
    "sort": _build_sort,
    "head": _build_head,
    "tail": _build_tail,
    "slice": _build_slice,
    "join_inner": _build_join_inner,
    "join_left": _build_join_left,
    "join_asof": _build_join_asof,
    "aggregate": _build_aggregate,
    "unique": _build_unique,
    "concat": _build_concat,
    "drop_nulls": _build_drop_nulls,
    "drop_nans": _build_drop_nans,
    "with_row_index": _build_with_row_index,
    "explode": _build_explode,
    "sample": _build_sample,
    "unpivot": _build_unpivot,
    "pivot": _build_pivot,
    "top_k": _build_top_k,
    "unnest": _build_unnest,
    "source": _build_source,
}


# ── Exception set ────────────────────────────────────────────────────────
# (operation_name, backend_name) → "reason. Since YYYY-MM-DD."
_KNOWN_REL_SMOKE_FAILURES: dict[tuple[str, str], str] = {
    # join_asof: Narwhals/pandas backends pass an unexpected `tolerance` kwarg
    # to the underlying DataFrame.join_asof() call.
    ("join_asof", "pandas"): (
        "TypeError: DataFrame.join_asof() got an unexpected keyword argument "
        "'tolerance'. Narwhals backend passes tolerance kwarg unconditionally. "
        "Since 2026-05-18."
    ),
    ("join_asof", "narwhals-polars"): (
        "TypeError: DataFrame.join_asof() got an unexpected keyword argument "
        "'tolerance'. Narwhals backend passes tolerance kwarg unconditionally. "
        "Since 2026-05-18."
    ),
    ("join_asof", "narwhals-pandas"): (
        "TypeError: DataFrame.join_asof() got an unexpected keyword argument "
        "'tolerance'. Narwhals backend passes tolerance kwarg unconditionally. "
        "Since 2026-05-18."
    ),
    # explode: pandas/narwhals-pandas wraps pandas which has Object dtype for
    # Python lists — Narwhals InvalidOperationError: explode requires List type.
    ("explode", "pandas"): (
        "InvalidOperationError: explode operation not supported for dtype "
        "Object — narwhals-wrapped pandas frames store Python lists as Object "
        "columns, not typed List columns. Since 2026-05-18."
    ),
    ("explode", "narwhals-pandas"): (
        "InvalidOperationError: explode operation not supported for dtype "
        "Object — narwhals-wrapped pandas frames store Python lists as Object "
        "columns, not typed List columns. Since 2026-05-18."
    ),
    # explode: SQLite does not support Array/List column types.
    ("explode", "ibis-sqlite"): (
        "UnsupportedBackendType: Array types aren't supported in SQLite. "
        "Since 2026-05-18."
    ),
    # pivot: ibis pivot_wider() API does not accept an `on` keyword argument
    # — parameter name mismatch between mountainash relay and ibis API.
    ("pivot", "ibis-polars"): (
        "TypeError: Table.pivot_wider() got an unexpected keyword argument 'on'. "
        "Ibis pivot_wider() uses different param names than mountainash relay. "
        "Since 2026-05-18."
    ),
    ("pivot", "ibis-duckdb"): (
        "TypeError: Table.pivot_wider() got an unexpected keyword argument 'on'. "
        "Ibis pivot_wider() uses different param names than mountainash relay. "
        "Since 2026-05-18."
    ),
    ("pivot", "ibis-sqlite"): (
        "TypeError: Table.pivot_wider() got an unexpected keyword argument 'on'. "
        "Ibis pivot_wider() uses different param names than mountainash relay. "
        "Since 2026-05-18."
    ),
    # unnest: Narwhals backend not yet implemented (Phase 2 work).
    ("unnest", "pandas"): (
        "NotImplementedError: unnest is not supported on the Narwhals backend — "
        "requires schema introspection synthesis (Phase 2). Since 2026-05-18."
    ),
    ("unnest", "narwhals-polars"): (
        "NotImplementedError: unnest is not supported on the Narwhals backend — "
        "requires schema introspection synthesis (Phase 2). Since 2026-05-18."
    ),
    ("unnest", "narwhals-pandas"): (
        "NotImplementedError: unnest is not supported on the Narwhals backend — "
        "requires schema introspection synthesis (Phase 2). Since 2026-05-18."
    ),
    # unnest: SQLite does not support Struct column types.
    ("unnest", "ibis-sqlite"): (
        "UnsupportedBackendType: Struct types aren't supported in SQLite. "
        "Since 2026-05-18."
    ),
    # source: SourceRelNode always materialises via Polars (pydata ingress).
    # Non-Polars backends pass silently without exercising their backend path.
    ("source", "pandas"): "SourceRelNode always routes through Polars, not this backend. Since 2026-05-18.",
    ("source", "narwhals-polars"): "SourceRelNode always routes through Polars, not this backend. Since 2026-05-18.",
    ("source", "narwhals-pandas"): "SourceRelNode always routes through Polars, not this backend. Since 2026-05-18.",
    ("source", "ibis-polars"): "SourceRelNode always routes through Polars, not this backend. Since 2026-05-18.",
    ("source", "ibis-duckdb"): "SourceRelNode always routes through Polars, not this backend. Since 2026-05-18.",
    ("source", "ibis-sqlite"): "SourceRelNode always routes through Polars, not this backend. Since 2026-05-18.",
}


# ── Collect test cases ───────────────────────────────────────────────────


def _collect_smoke_cases() -> list[tuple[str, str]]:
    cases = []
    for op_name in _OPERATIONS:
        for backend in ALL_BACKENDS:
            cases.append((op_name, backend))
    return cases


_SMOKE_CASES = _collect_smoke_cases()


# ── Test class ───────────────────────────────────────────────────────────


class TestRelCollectSmoke:
    """Every registered relation operation must collect on every backend."""

    @pytest.mark.parametrize(
        ("op_name", "backend_name"),
        _SMOKE_CASES,
        ids=[f"{op}/{bn}" for op, bn in _SMOKE_CASES],
    )
    def test_collect_succeeds(
        self, op_name: str, backend_name: str, backend_factory
    ) -> None:
        key = (op_name, backend_name)
        if key in _KNOWN_REL_SMOKE_FAILURES:
            pytest.xfail(_KNOWN_REL_SMOKE_FAILURES[key])

        override = _SMOKE_FIXTURE_OVERRIDES.get(op_name, {})
        data = override.get("data", _DEFAULT_DATA)
        right_data = override.get("right_data", _RIGHT_DATA)

        # For join operations on ibis backends both tables must share a
        # connection — use create_pair so the visitor can execute cross-table
        # operations without a "table not found" error.
        join_ops = {"join_inner", "join_left", "join_asof"}
        if op_name in join_ops and backend_name.startswith("ibis-"):
            df, df_right = backend_factory.create_pair(
                data, right_data, backend_name
            )
        else:
            df = backend_factory.create(data, backend_name)
            df_right = backend_factory.create(right_data, backend_name)

        builder = _OPERATIONS[op_name]
        try:
            builder(df, df_right)
        except Exception as e:
            pytest.fail(
                f"{op_name} on {backend_name}: collect() raised "
                f"{type(e).__name__}: {e}"
            )


# ── Meta-tests ───────────────────────────────────────────────────────────


class TestRelSmokeExceptionSetIntegrity:
    """Validate the exception set format and freshness."""

    def test_every_entry_has_reason_and_date(self) -> None:
        for key, reason in _KNOWN_REL_SMOKE_FAILURES.items():
            assert "since" in reason.lower(), (
                f"_KNOWN_REL_SMOKE_FAILURES[{key}] missing date: {reason!r}"
            )
            assert re.search(r"\d{4}-\d{2}-\d{2}", reason), (
                f"_KNOWN_REL_SMOKE_FAILURES[{key}] no date found: {reason!r}"
            )

    def test_every_entry_resolves_to_real_op_and_backend(self) -> None:
        valid_ops = set(_OPERATIONS.keys())
        valid_backends = set(ALL_BACKENDS)
        for op_name, bn in _KNOWN_REL_SMOKE_FAILURES:
            assert op_name in valid_ops, (
                f"_KNOWN_REL_SMOKE_FAILURES: operation {op_name!r} not in _OPERATIONS"
            )
            assert bn in valid_backends, (
                f"_KNOWN_REL_SMOKE_FAILURES: backend {bn!r} not valid"
            )

    def test_extension_ops_covered_in_operations(self) -> None:
        """Every non-registry-handled ExtensionRelOperation must have a smoke test."""
        from mountainash.core.constants import ExtensionRelOperation

        _REGISTRY_HANDLED = {"REF", "READ_RESOURCE"}
        enum_ops = {
            op.name.lower()
            for op in ExtensionRelOperation
            if op.name not in _REGISTRY_HANDLED
        }
        covered = set(_OPERATIONS.keys())
        missing = enum_ops - covered
        assert not missing, (
            f"ExtensionRelOperation members without smoke test: {sorted(missing)}. "
            f"Add a builder to _OPERATIONS or document in the exception set."
        )
