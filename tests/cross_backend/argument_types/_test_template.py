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
    complex_builder: Callable[[str], Any] | None = None
    execution_mode: str = "select"


def _materialize_arg(
    input_type: str,
    raw: Any,
    col_name: str,
    complex_builder: Callable[[str], Any] | None = None,
):
    """Produce the argument value for a given input type."""
    if input_type == "raw":
        return raw
    if input_type == "lit":
        return ma.lit(raw)
    if input_type == "col":
        return ma.col(col_name)
    if input_type == "complex":
        if complex_builder is not None:
            return complex_builder(col_name)
        if isinstance(raw, str):
            return ma.col(col_name).str.lower()
        return ma.col(col_name).add(ma.lit(0))
    raise ValueError(input_type)


def _get_registry(backend: str):
    if backend == "polars":
        from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem as B
    elif backend == "ibis":
        from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem as B
    elif backend in ("narwhals-polars", "narwhals-pandas"):
        from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem as B
    else:
        raise ValueError(backend)
    return B.KNOWN_EXPR_LIMITATIONS


def xfail_if_limited(backend: str, function_key: Any, param_name: str, input_type: str):
    """Returns a pytest.mark.xfail if the registry declares this combination limited,
    and the input type actually exercises the limitation (col/complex, not raw/lit).

    The narwhals KNOWN_EXPR_LIMITATIONS registry is shared between narwhals-polars
    and narwhals-pandas, but the actual native-backend behaviour differs: narwhals
    wrapping polars sometimes accepts expressions the registry flags (in particular
    anything narwhals itself has learned to pass through to polars). Rather than
    maintain two parallel registries, we keep a small allow-list of
    (function_key, param_name) pairs that are known to work on narwhals-polars
    despite the registry entry, and skip the xfail for those on that variant only.
    When upstream narwhals extends support further, entries are added to the
    allow-list and the registry entry itself is kept to enrich narwhals-pandas
    errors until both variants work.
    """
    if input_type in ("raw", "lit"):
        return None
    if backend == "narwhals-polars":
        # narwhals 2.19.0 added Expr support for str.contains on polars.
        # Extend this list as upstream closes more gaps; see
        # h.backlog/narwhals-219-upgrade.md.
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_SUBSTRAIT_SCALAR_STRING as _FK_STR,
        )
        _NW_POLARS_FIXED: set[tuple[Any, str]] = {
            (_FK_STR.CONTAINS, "substring"),
            (_FK_STR.STARTS_WITH, "substring"),
            (_FK_STR.ENDS_WITH, "substring"),
            (_FK_STR.LIKE, "match"),
            (_FK_STR.REPLACE, "replacement"),
            (_FK_STR.REGEXP_REPLACE, "replacement"),
        }
        if (function_key, param_name) in _NW_POLARS_FIXED:
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


def _materialize_result(df, compiled, backend: str) -> None:
    """Force execution to surface errors that fire at materialization time."""
    if backend == "polars":
        import polars as pl

        if isinstance(df, pl.LazyFrame):
            df.select(compiled).collect()
        else:
            df.select(compiled)
    elif backend == "ibis":
        df.select(compiled.name("__result__")).execute()
    elif backend in ("narwhals-polars", "narwhals-pandas"):
        df.select(compiled).to_native()
    else:
        raise ValueError(backend)


def run_argument_matrix(op: OpSpec, backend: str, input_type: str):
    """Execute one cell of the (operation × backend × input_type) matrix."""
    from cross_backend.argument_types.conftest import make_df

    df = make_df(op.data, backend)
    arg = _materialize_arg(input_type, op.raw_arg, op.arg_col_name, op.complex_builder)
    expr = op.build(ma.col(op.input_col), arg)
    if op.execution_mode == "over":
        expr = expr.over("__group__")

    registry = _get_registry(backend)
    limitation = registry.get((op.function_key, op.param_name))

    try:
        compiled = expr.compile(df)
        assert compiled is not None
        _materialize_result(df, compiled, backend)
    except BackendCapabilityError:
        raise
    except Exception as e:
        if limitation is not None and isinstance(e, limitation.native_errors):
            raise BackendCapabilityError(
                str(limitation.message),
                backend=backend,
                function_key=op.function_key,
                limitation=limitation,
            ) from e
        raise
