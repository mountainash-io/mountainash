"""Empirical API-reachability guard (spec 2026-07-28 §3.1).

Registry resolution proves FKEY<->protocol identity, NOT that any public entry
point emits the FKEY.  An op can have an enum, a protocol method and a def while
no builder method emits it -- the condition afflicting `extract` and
`round_temporal` today.  This guard is structural: it invokes a public entry
point and asserts the emitted node's function_key.
"""
from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import pytest

import mountainash as ma
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)

_TESTS_DIR = str(Path(__file__).resolve().parent.parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from core._smoke_helpers import build_args_for_fkey, is_non_expression_fkey
from core.test_compile_smoke import _resolve_api_callable


def _builders() -> dict[Enum, Callable[[], Any]]:
    """Public entry points the generic resolver cannot construct."""
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_DATETIME as MD,
        FKEY_MOUNTAINASH_SCALAR_LIST as ML,
        FKEY_MOUNTAINASH_SCALAR_STRUCT as MS,
        FKEY_MOUNTAINASH_SCALAR_TERNARY as MT,
        FKEY_MOUNTAINASH_WINDOW as MW,
        FKEY_SUBSTRAIT_SCALAR_AGGREGATE as SA,
        FKEY_SUBSTRAIT_SCALAR_DATETIME as SD,
        FKEY_SUBSTRAIT_SCALAR_LOGARITHMIC as SL,
        SUBSTRAIT_ARITHMETIC_WINDOW as SW,
    )

    c = ma.col("a")
    s = ma.col("c")
    b = ma.col("e")
    return {
        # Options with no auto-constructible default.
        MD.OFFSET_BY: lambda: c.dt.offset_by("1d"),
        MD.TRUNCATE: lambda: c.dt.truncate("day"),
        MD.CEIL: lambda: c.dt.ceil("day"),
        MD.FLOOR: lambda: c.dt.floor("day"),
        MD.ROUND: lambda: c.dt.round("day"),
        ML.GET: lambda: c.list.get(0),
        ML.TO_ARRAY: lambda: c.list.to_array(width=2),
        MS.FIELD: lambda: c.struct.field("x"),
        SW.NTILE: lambda: c.ntile(4).over("b"),
        # Namespace collision: the generic resolver finds list.median first.
        SA.MEDIAN: lambda: ma.median(0, c),
        # Default method= emits the MA alias key, not the Substrait canonical.
        SW.RANK: lambda: c.rank(method="min").over("b"),
        # Ternary ops: protocol method name differs from public API name.
        MT.ALWAYS_TRUE: lambda: ma.always_true(),
        MT.ALWAYS_FALSE: lambda: ma.always_false(),
        MT.IS_TRUE: lambda: c.t_is_true(),
        MT.IS_FALSE: lambda: c.t_is_false(),
        MT.IS_UNKNOWN: lambda: c.t_is_unknown(),
        MT.IS_KNOWN: lambda: c.t_is_known(),
        MT.MAYBE_TRUE: lambda: c.t_maybe_true(),
        MT.MAYBE_FALSE: lambda: c.t_maybe_false(),
        # Aggregate: protocol method name differs from public API name.
        SA.BOOL_AND: lambda: b.all(),
        SA.BOOL_OR: lambda: b.any(),
        # Datetime: requires .str namespace traversal.
        SD.STRPTIME_DATE: lambda: s.str.to_date("%Y-%m-%d"),
        SD.STRPTIME_TIMESTAMP: lambda: s.str.to_datetime("%Y-%m-%d"),
        # Logarithmic: protocol method name differs.
        SL.LOGB: lambda: c.log(base=10),
        # Window functions needing .over() context.
        SW.ROW_NUMBER: lambda: c.row_number().over("b"),
        SW.DENSE_RANK: lambda: c.dense_rank().over("b"),
        SW.PERCENT_RANK: lambda: c.percent_rank().over("b"),
        SW.CUME_DIST: lambda: c.cume_dist().over("b"),
        # Rank variants: method= param disambiguates.
        MW.RANK_MAX: lambda: c.rank(method="max").over("b"),
        MW.RANK_AVERAGE: lambda: c.rank(method="average").over("b"),
    }


_UNREACHABLE_FKEYS: dict[str, str] = {
    "FKEY_SUBSTRAIT_CAST.CAST": (
        "emits CastNode, a distinct AST node type with no function_key; "
        "reachable via Expression.cast() and covered by test_cast.py"
    ),
    "FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE": (
        "emits IfThenNode, a distinct AST node type with no function_key; "
        "reachable via ma.when().then().otherwise()"
    ),
    "FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES": (
        "AST-internal marker node, not a compilable expression"
    ),
    "FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT": (
        "no public builder method emits the canonical Substrait EXTRACT key -- "
        "dt.year() and friends emit their own MA keys; wired by PR-C "
        "(backlog: substrait-datetime-missing-ops)"
    ),
    "FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN": (
        "no public builder method emits the canonical Substrait EXTRACT_BOOLEAN key -- "
        "dt.is_leap_year() emits FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_LEAP_YEAR; "
        "wired by PR-C (backlog: substrait-datetime-missing-ops)"
    ),
}


def _emit(fkey: Enum) -> Enum | None:
    """Build via a public entry point; return the emitted function_key."""
    builders = _builders()
    if fkey in builders:
        return getattr(builders[fkey]()._node, "function_key", None)

    fdef = ExpressionFunctionRegistry.get(fkey)
    args, options = build_args_for_fkey(fkey, fdef)
    name = fdef.protocol_method.__name__
    if not args:
        free_fn = getattr(ma, name, None)
        if free_fn is None:
            return None
        return getattr(free_fn(**options)._node, "function_key", None)
    method = _resolve_api_callable(args[0], name)
    if method is None:
        free_fn = getattr(ma, name, None)
        if free_fn is None:
            return None
        return getattr(free_fn(*args, **options)._node, "function_key", None)
    return getattr(method(*args[1:], **options)._node, "function_key", None)


def _all_fkeys() -> list[Enum]:
    ExpressionFunctionRegistry._init_registry()
    return sorted(ExpressionFunctionRegistry._functions, key=str)


@pytest.mark.parametrize("fkey", _all_fkeys(), ids=str)
def test_fkey_is_emitted_by_a_public_entry_point(fkey: Enum) -> None:
    if str(fkey) in _UNREACHABLE_FKEYS:
        pytest.xfail(f"{fkey}: {_UNREACHABLE_FKEYS[str(fkey)]}")
    emitted = _emit(fkey)
    assert emitted == fkey, (
        f"{fkey} is not emitted by any public API entry point "
        f"(got {emitted!r}). Either wire a builder method, add a public entry "
        f"point to _builders(), or park it in _UNREACHABLE_FKEYS with a reason."
    )


def test_no_parked_fkey_is_actually_reachable() -> None:
    """Closed-by-default: a park that became reachable must be drained."""
    ExpressionFunctionRegistry._init_registry()
    by_name = {str(fkey): fkey for fkey in ExpressionFunctionRegistry._functions}
    stale = []
    for name in _UNREACHABLE_FKEYS:
        fkey = by_name.get(name)
        assert fkey is not None, f"_UNREACHABLE_FKEYS names {name}, not in the registry"
        try:
            if _emit(fkey) == fkey:
                stale.append(name)
        except Exception:
            continue
    assert not stale, f"parked but now reachable — drain from _UNREACHABLE_FKEYS: {stale}"


def test_every_park_has_a_reason() -> None:
    empty = [name for name, reason in _UNREACHABLE_FKEYS.items() if not reason.strip()]
    assert not empty, f"_UNREACHABLE_FKEYS entries with no reason: {empty}"
