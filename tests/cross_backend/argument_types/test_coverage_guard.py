"""Meta-tests for argument/option parameter classification.

- test_every_argument_param_is_tested: every argument-kind protocol param has a TESTED_PARAMS entry
- test_no_unclassified_params: no ambiguously-typed params in protocols
- test_option_params_not_widened_by_backends: option-typed protocol params are not widened to
  accept expressions in any backend implementation (mixed-capability drift detection)
"""
from __future__ import annotations

import inspect
import typing
from typing import get_type_hints
import importlib

from cross_backend.argument_types._introspection import (
    introspect_protocols,
    _iter_protocol_classes,
    _CATEGORY_MAP,
)

_CATEGORY_MODULES = [
    "test_arg_types_string",
    "test_arg_types_arithmetic",
    "test_arg_types_comparison",
    "test_arg_types_boolean",
    "test_arg_types_null",
    "test_arg_types_rounding",
    "test_arg_types_logarithmic",
    "test_arg_types_datetime",
    "test_arg_types_name",
    "test_arg_types_window",
    "test_arg_types_aggregate",
    "test_arg_types_misc",
    "test_arg_types_list",
    "test_arg_types_struct",
]


def _collect_tested_params() -> set[tuple[str, str]]:
    tested: set[tuple[str, str]] = set()
    for modname in _CATEGORY_MODULES:
        try:
            mod = importlib.import_module(f"cross_backend.argument_types.{modname}")
        except ImportError:
            continue
        for fkey, pname in getattr(mod, "TESTED_PARAMS", []):
            op_name = fkey.name.lower() if hasattr(fkey, "name") else str(fkey)
            tested.add((op_name, pname))
    return tested


_KNOWN_UNTESTED_ARGUMENT_PARAMS: set[tuple[str, str]] = {
    # These argument-typed protocol params have no cross-backend argument type
    # test yet. Adding a param here is acceptable ONLY when registering a
    # previously-untracked protocol in _CATEGORY_MAP. New operations should add
    # tests, not entries here. Shrink this set over time.
    #
    # -- datetime (unimplemented APIs) --
    ("add_intervals", "y"),
    ("diff_milliseconds", "other"),
    # -- string (substrait) — broken APIs --
    ("string_split", "separator"),
    ("concat_ws", "string_arguments"),
    ("regexp_count_substring", "pattern"), ("regexp_count_substring", "position"),
    ("regexp_strpos", "pattern"), ("regexp_strpos", "position"), ("regexp_strpos", "occurrence"),
    ("regexp_match_substring", "pattern"), ("regexp_match_substring", "position"),
    ("regexp_match_substring", "occurrence"), ("regexp_match_substring", "group"),
    ("regexp_match_substring_all", "pattern"), ("regexp_match_substring_all", "position"),
    ("regexp_match_substring_all", "group"),
    ("regexp_string_split", "pattern"),
}


def test_every_argument_param_is_tested():
    introspected = {
        (p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "argument"
    }
    tested = _collect_tested_params()
    newly_missing = {
        (op, pname) for op, pname in introspected
        if (op, pname) not in tested and (op, pname) not in _KNOWN_UNTESTED_ARGUMENT_PARAMS
    }
    extra = {(op, pname) for op, pname in tested if (op, pname) not in introspected}
    stale_known = _KNOWN_UNTESTED_ARGUMENT_PARAMS - introspected
    assert not newly_missing, f"New argument params with no test (add test or register in _KNOWN_UNTESTED): {sorted(newly_missing)}"
    assert not extra, f"Tested params with no protocol: {sorted(extra)}"
    assert not stale_known, f"Entries in _KNOWN_UNTESTED_ARGUMENT_PARAMS that no longer exist in protocols (remove them): {sorted(stale_known)}"
    overlap = _KNOWN_UNTESTED_ARGUMENT_PARAMS & tested
    assert not overlap, (
        f"Entries in _KNOWN_UNTESTED_ARGUMENT_PARAMS that are already tested "
        f"(remove from _KNOWN_UNTESTED): {sorted(overlap)}"
    )


def test_all_protocols_categorized():
    """Every protocol class discovered by _iter_protocol_classes must be in _CATEGORY_MAP."""
    uncategorized = [name for name, _ in _iter_protocol_classes() if name not in _CATEGORY_MAP]
    assert uncategorized == [], f"Uncategorized protocols (add to _CATEGORY_MAP): {uncategorized}"


def test_no_unclassified_params():
    unclassified = [p for p in introspect_protocols() if p.kind == "unclassified"]
    assert not unclassified, (
        f"Protocol params with ambiguous typing (fix in Phase 0): "
        f"{[(p.protocol_name, p.op_name, p.param_name, p.annotation) for p in unclassified]}"
    )


def test_all_protocols_registered_in_category_map():
    """Every expression system protocol must be registered in _CATEGORY_MAP.

    If this fails, a new protocol was added but not registered in
    _introspection._CATEGORY_MAP. Add it with the appropriate category
    so drift detection covers it.
    """
    from cross_backend.argument_types._introspection import _iter_protocol_classes, _CATEGORY_MAP

    unregistered = [
        name for name, _ in _iter_protocol_classes()
        if name not in _CATEGORY_MAP
    ]
    assert not unregistered, (
        f"Expression system protocols not in _CATEGORY_MAP "
        f"(add them to _introspection._CATEGORY_MAP): {sorted(unregistered)}"
    )


# ---------------------------------------------------------------------------
# Mixed-capability drift detection
# ---------------------------------------------------------------------------

_BACKEND_CLASSES: list[tuple[str, type]] = []


def _get_backend_classes() -> list[tuple[str, type]]:
    """Lazily import the three composed expression system classes."""
    if _BACKEND_CLASSES:
        return _BACKEND_CLASSES
    from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
    from mountainash.expressions.backends.expression_systems.ibis import IbisExpressionSystem
    from mountainash.expressions.backends.expression_systems.narwhals import NarwhalsExpressionSystem
    _BACKEND_CLASSES.extend([
        ("Polars", PolarsExpressionSystem),
        ("Ibis", IbisExpressionSystem),
        ("Narwhals", NarwhalsExpressionSystem),
    ])
    return _BACKEND_CLASSES


_EXPR_TYPE_MARKERS = {"Expr", "ExpressionT", "PolarsExpr", "NarwhalsExpr", "IbisNumericExpr",
                      "IbisValueExpr", "IbisBooleanExpr", "IbisStringExpr", "IbisColumnExpr"}


def _backend_accepts_expr(backend_cls: type, method_name: str, param_name: str) -> bool:
    """Check if a backend method's parameter annotation suggests it accepts expressions."""
    method = getattr(backend_cls, method_name, None)
    if method is None:
        return False
    try:
        hints = get_type_hints(method)
    except Exception:
        hints = {}
    sig = inspect.signature(method)
    param = sig.parameters.get(param_name)
    if param is None:
        return False
    ann = hints.get(param_name, param.annotation)
    ann_str = str(ann)
    if any(marker in ann_str for marker in _EXPR_TYPE_MARKERS):
        return True
    origin = typing.get_origin(ann)
    if origin is typing.Union:
        return any(any(m in str(a) for m in _EXPR_TYPE_MARKERS) for a in typing.get_args(ann))
    return False


def test_option_params_not_widened_by_backends():
    """Detect mixed-capability drift: option-typed protocol params that a backend widens.

    If a backend accepts expressions for a parameter that the protocol types as
    option (concrete int/str/bool), the protocol needs updating to argument channel.
    See: e.cross-backend/arguments-vs-options.md "Mixed-capability parameters".
    """
    option_params = [p for p in introspect_protocols() if p.kind == "option"]
    mismatches = []
    for p in option_params:
        for backend_name, backend_cls in _get_backend_classes():
            if _backend_accepts_expr(backend_cls, p.op_name, p.param_name):
                mismatches.append(
                    f"{p.protocol_name}.{p.op_name}({p.param_name}) is option "
                    f"in protocol but {backend_name} accepts expressions"
                )
    assert not mismatches, (
        "Option-typed protocol params widened by backends (should be arguments):\n"
        + "\n".join(f"  - {m}" for m in mismatches)
    )
