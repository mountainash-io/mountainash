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

from cross_backend.argument_types._introspection import introspect_protocols

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


def test_every_argument_param_is_tested():
    introspected = {
        (p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "argument"
    }
    tested = _collect_tested_params()
    missing = {(op, pname) for op, pname in introspected if (op, pname) not in tested}
    extra = {(op, pname) for op, pname in tested if (op, pname) not in introspected}
    assert not missing, f"Argument params with no test: {sorted(missing)}"
    assert not extra, f"Tested params with no protocol: {sorted(extra)}"


def test_no_unclassified_params():
    unclassified = [p for p in introspect_protocols() if p.kind == "unclassified"]
    assert not unclassified, (
        f"Protocol params with ambiguous typing (fix in Phase 0): "
        f"{[(p.protocol_name, p.op_name, p.param_name, p.annotation) for p in unclassified]}"
    )


# ---------------------------------------------------------------------------
# Mixed-capability drift detection
# ---------------------------------------------------------------------------
# Per arguments-vs-options principle: if ANY backend accepts an expression for
# a parameter, the protocol must type it as ExpressionT (argument channel).
# This test catches drift where a backend widens a parameter to accept
# expressions but the protocol still types it as a concrete option.

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
