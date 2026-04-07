"""Shared helpers used by every test_arg_types_<category>.py file.

Each per-category file declares:
    TESTED_PARAMS: list[tuple[Any, str]]  # (function_key, param_name)
    OP_SPECS: list[OpSpec]                # one entry per operation under test

Then calls run_argument_matrix(op_spec, backend, input_type) per parametrized case.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError

INPUT_TYPES = ["raw", "lit", "col", "complex"]


@dataclass
class OpSpec:
    """Describes a single operation under test."""
    function_key: Any
    op_name: str
    build: Callable[[Any, Any], Any]
    raw_arg: Any
    arg_col_name: str
    param_name: str
    data: dict[str, list[Any]]
    input_col: str = "text"
    extra: dict[str, Any] = field(default_factory=dict)


def _materialize_arg(input_type: str, raw: Any, col_name: str):
    """Produce the argument value for a given input type."""
    if input_type == "raw":
        return raw
    if input_type == "lit":
        return ma.lit(raw)
    if input_type == "col":
        return ma.col(col_name)
    if input_type == "complex":
        if isinstance(raw, str):
            return ma.col(col_name).str.lower()
        return ma.col(col_name).add(ma.lit(0))
    raise ValueError(input_type)


def _get_registry(backend: str):
    if backend == "polars":
        from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem as B
    elif backend == "ibis":
        from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem as B
    elif backend == "narwhals":
        from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem as B
    else:
        raise ValueError(backend)
    return B.KNOWN_EXPR_LIMITATIONS


def xfail_if_limited(backend: str, function_key: Any, param_name: str, input_type: str):
    """Returns a pytest.mark.xfail if the registry declares this combination limited,
    and the input type actually exercises the limitation (col/complex, not raw/lit)."""
    if input_type in ("raw", "lit"):
        return None
    registry = _get_registry(backend)
    limitation = registry.get((function_key, param_name))
    if limitation is None:
        return None
    return pytest.mark.xfail(
        strict=True,
        raises=BackendCapabilityError,
        reason=limitation.message,
    )


def run_argument_matrix(op: OpSpec, backend: str, input_type: str):
    """Execute one cell of the (operation × backend × input_type) matrix."""
    from cross_backend.argument_types.conftest import make_df

    df = make_df(op.data, backend)
    arg = _materialize_arg(input_type, op.raw_arg, op.arg_col_name)
    expr = op.build(ma.col(op.input_col), arg)
    compiled = expr.compile(df)
    assert compiled is not None
