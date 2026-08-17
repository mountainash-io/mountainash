"""Shared helpers for introspection-driven expression construction.

Builds minimal valid expressions for any FKEY by introspecting the protocol
method signature. Used by test_signature_conformance.py (A2) and
test_compile_smoke.py (Gap B).
"""
from __future__ import annotations

import inspect
import typing
from enum import Enum
from typing import Any, Callable

import mountainash as ma
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionDef,
    ExpressionFunctionRegistry,
)
import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent.parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from expressions.argument_types._introspection import _classify_annotation

_STRING_CATEGORIES = {"string"}
_BOOLEAN_CATEGORIES = {"boolean"}

_DEFAULT_COLS = ["a", "b", "f", "g", "h"]
_STRING_COLS = ["c"]
_FLOAT_COLS = ["d"]
_BOOL_COLS = ["e"]

def _init_smoke_overrides() -> dict[Enum, tuple[list[Any], dict[str, Any]]]:
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_DATETIME,
        FKEY_SUBSTRAIT_CAST,
        FKEY_SUBSTRAIT_SCALAR_DATETIME,
    )

    return {
        FKEY_SUBSTRAIT_CAST.CAST: ([ma.col("a")], {"dtype": "str"}),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.ASSUME_TIMEZONE: ([ma.col("a"), "UTC"], {}),
        FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE: ([ma.col("a"), "UTC"], {}),
        FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST: ([ma.col("a"), "UTC"], {}),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.LOCAL_TIMESTAMP: ([ma.col("a"), "UTC"], {}),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL: (
            [ma.col("a")],
            {"rounding": "FLOOR", "unit": "DAY"},
        ),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR: (
            [ma.col("a")],
            {"rounding": "FLOOR", "unit": "MONTH"},
        ),
    }



_SMOKE_ARG_OVERRIDES: dict[Enum, tuple[list[Any], dict[str, Any]]] = _init_smoke_overrides()


def _get_category_for_fkey(fkey: Enum) -> str | None:
    from expressions.argument_types._introspection import _CATEGORY_MAP

    fdef = ExpressionFunctionRegistry.get(fkey)
    if fdef.protocol_method is None:
        return None
    qualname = fdef.protocol_method.__qualname__
    class_name = qualname.split(".")[0] if "." in qualname else None
    if class_name:
        return _CATEGORY_MAP.get(class_name)
    return None


def _pick_col(category: str | None, idx: int) -> Any:
    if category in _STRING_CATEGORIES:
        return ma.col(_STRING_COLS[0])
    if category in _BOOLEAN_CATEGORIES:
        return ma.col(_BOOL_COLS[0])
    if idx < len(_DEFAULT_COLS):
        return ma.col(_DEFAULT_COLS[idx])
    return ma.col("a")


def _default_for_option(name: str) -> Any:
    _OPTION_DEFAULTS: dict[str, Any] = {
        "overflow": "SILENT",
        "rounding": "TIE_TO_EVEN",
        "closed": "both",
        "separator": ",",
        "pattern": ".*",
        "format": "%Y-%m-%d",
        "component": "year",
        "base": 10,
        "encoding": "utf-8",
        "strict": True,
        "ignore_nulls": True,
        "json_path": "$.a",
        "dtype": "str",
        "suffix": "x",
        "s": 0,
        "negative_start": None,
    }
    return _OPTION_DEFAULTS.get(name)


def build_args_for_fkey(
    fkey: Enum,
    fdef: ExpressionFunctionDef,
) -> tuple[list[Any], dict[str, Any]]:
    """Build (positional_args, options) for a FKEY via introspection.

    Raises ValueError if the FKEY needs a manual override.
    """
    if fkey in _SMOKE_ARG_OVERRIDES:
        return _SMOKE_ARG_OVERRIDES[fkey]

    if fdef.protocol_method is None:
        raise ValueError(f"{fkey} has no protocol_method")

    sig = inspect.signature(fdef.protocol_method)
    hints = typing.get_type_hints(fdef.protocol_method)
    category = _get_category_for_fkey(fkey)

    args: list[Any] = []
    options: dict[str, Any] = {}
    col_idx = 0

    for pname, param in sig.parameters.items():
        if pname == "self":
            continue

        ann = hints.get(pname, param.annotation)
        kind = _classify_annotation(ann)

        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            args.append(_pick_col(category, 0))
            args.append(_pick_col(category, 1))
            continue

        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            default = _default_for_option(pname)
            if default is not None:
                options[pname] = default
            continue

        if kind == "argument":
            args.append(_pick_col(category, col_idx))
            col_idx += 1
            continue

        if param.default is not inspect.Parameter.empty:
            continue

        ann_str = str(ann)
        if "int" in ann_str:
            args.append(1)
        elif "float" in ann_str:
            args.append(1.0)
        elif "str" in ann_str:
            args.append("x")
        elif "bool" in ann_str:
            args.append(True)
        else:
            raise ValueError(
                f"{fkey}: cannot auto-construct arg '{pname}' with annotation "
                f"'{ann}'. Add an entry to _SMOKE_ARG_OVERRIDES."
            )

    return args, options


_SENTINEL_MISSING = object()

_SMOKE_EXPR_BUILDERS: dict[Enum, Any] | None = None


def _init_shared_fkey_builders() -> dict[Enum, Callable[[], Any]]:
    # retirement-verdict: front-4.3 — shared source for the byte-identical FKEY->public-call entries formerly duplicated in test_api_reachability + _smoke_helpers.
    """FKEY -> public-call entries that are byte-identical between
    `tests/core/test_api_reachability._builders()` and
    `_smoke_helpers._init_smoke_expr_builders()`. Each consumer merges this
    base with its own local overrides (divergent RANK + consumer-specific
    arg-construction or composite patterns).

    Intentionally excludes `SUBSTRAIT_ARITHMETIC_WINDOW.RANK` — that entry
    is divergent: the reachability guard forces the canonical Substrait
    `method="min"` form while the smoke harness uses the default form.
    """
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_TERNARY,
        FKEY_MOUNTAINASH_WINDOW,
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
        FKEY_SUBSTRAIT_SCALAR_DATETIME,
        FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC,
        SUBSTRAIT_ARITHMETIC_WINDOW,
    )

    c = ma.col("a")
    s = ma.col("c")
    b = ma.col("e")

    return {
        FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_TRUE: lambda: ma.always_true(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.ALWAYS_FALSE: lambda: ma.always_false(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_TRUE: lambda: c.t_is_true(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_FALSE: lambda: c.t_is_false(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_UNKNOWN: lambda: c.t_is_unknown(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_KNOWN: lambda: c.t_is_known(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_TRUE: lambda: c.t_maybe_true(),
        FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_FALSE: lambda: c.t_maybe_false(),
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE.BOOL_AND: lambda: b.all(),
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE.BOOL_OR: lambda: b.any(),
        FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC.LOGB: lambda: c.log(base=10),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE: lambda: s.str.to_date("%Y-%m-%d"),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP: lambda: s.str.to_datetime("%Y-%m-%d"),
        SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER: lambda: c.row_number().over("b"),
        SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK: lambda: c.dense_rank().over("b"),
        SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK: lambda: c.percent_rank().over("b"),
        SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST: lambda: c.cume_dist().over("b"),
        FKEY_MOUNTAINASH_WINDOW.RANK_MAX: lambda: c.rank(method="max").over("b"),
        FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE: lambda: c.rank(method="average").over("b"),
    }


def _init_smoke_expr_builders() -> dict[Enum, Any]:
    """FKEY -> expression factory for FKEYs where protocol method name
    doesn't match the public API accessor.

    Returns a dict mapping FKEY -> zero-arg callable returning an Expression,
    or None for FKEYs not reachable via the public API.
    """
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_CONDITIONAL,
        FKEY_SUBSTRAIT_SCALAR_DATETIME,
        SUBSTRAIT_ARITHMETIC_WINDOW,
    )

    c = ma.col("a")
    b = ma.col("e")

    return {
        **_init_shared_fkey_builders(),
        # Composite API pattern: reachable from a multi-step public call.
        FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE: lambda: ma.when(b).then(c).otherwise(c),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT: lambda: c.dt.year(),
        FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN: lambda: c.dt.is_leap_year(),
        # Divergent RANK: smoke harness uses the default form (no method=).
        SUBSTRAIT_ARITHMETIC_WINDOW.RANK: lambda: c.rank().over("b"),
    }


def get_smoke_expr_builder(fkey: Enum) -> Any:
    """Return an expression builder for fkey, or _SENTINEL_MISSING if not mapped."""
    global _SMOKE_EXPR_BUILDERS
    if _SMOKE_EXPR_BUILDERS is None:
        _SMOKE_EXPR_BUILDERS = _init_smoke_expr_builders()
    return _SMOKE_EXPR_BUILDERS.get(fkey, _SENTINEL_MISSING)


def _init_smoke_non_expression_fkeys() -> set[Enum]:
    """FKEYs that are AST-internal markers and don't produce compilable expressions."""
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_TERNARY,
    )
    return {
        FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES,
    }


_SMOKE_NON_EXPRESSION_FKEYS: set[Enum] | None = None


def is_non_expression_fkey(fkey: Enum) -> bool:
    """Return True if fkey is an AST-internal marker that cannot be compiled."""
    global _SMOKE_NON_EXPRESSION_FKEYS
    if _SMOKE_NON_EXPRESSION_FKEYS is None:
        _SMOKE_NON_EXPRESSION_FKEYS = _init_smoke_non_expression_fkeys()
    return fkey in _SMOKE_NON_EXPRESSION_FKEYS


def is_variadic(fdef: ExpressionFunctionDef) -> bool:
    if fdef.protocol_method is None:
        return False
    sig = inspect.signature(fdef.protocol_method)
    return any(
        p.kind == inspect.Parameter.VAR_POSITIONAL
        for p in sig.parameters.values()
    )


def count_protocol_arguments(fdef: ExpressionFunctionDef) -> int:
    """Count ExpressionT params in the protocol method (excluding self only).

    Returns -1 for variadic methods.
    """
    if fdef.protocol_method is None:
        return 0
    sig = inspect.signature(fdef.protocol_method)
    hints = typing.get_type_hints(fdef.protocol_method)

    count = 0
    for pname, param in sig.parameters.items():
        if pname == "self":
            continue
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return -1
        ann = hints.get(pname, param.annotation)
        if _classify_annotation(ann) == "argument":
            count += 1
    return count
