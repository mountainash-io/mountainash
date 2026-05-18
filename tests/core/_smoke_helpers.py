"""Shared helpers for introspection-driven expression construction.

Builds minimal valid expressions for any FKEY by introspecting the protocol
method signature. Used by test_signature_conformance.py (A2) and
test_compile_smoke.py (Gap B).
"""
from __future__ import annotations

import inspect
import typing
from enum import Enum
from typing import Any

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

_SMOKE_ARG_OVERRIDES: dict[Enum, tuple[list[Any], dict[str, Any]]] = {}


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
