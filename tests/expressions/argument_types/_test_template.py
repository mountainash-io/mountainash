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


_FIXTURE_IDENTITY = {
    # argument-types fixture name -> (family, dialect)
    "polars": ("polars", "polars"),
    "ibis": ("ibis", None),  # generic memtable ibis — family-level facts only
    "narwhals-polars": ("narwhals", "narwhals-polars"),
    "narwhals-pandas": ("narwhals", "narwhals-pandas"),
}


def _registry_lookup(backend: str, function_key, param_name: str):
    """Resolve a capability fact (new spine) or legacy KnownLimitation.

    During per-backend migration a backend may still carry its old
    KNOWN_EXPR_LIMITATIONS dict; consult the spine first, then fall back.
    """
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.constants import CONST_BACKEND

    family_name, dialect = _FIXTURE_IDENTITY[backend]
    fact = CapabilityRegistry.capability_for(
        function_key, param_name, CONST_BACKEND(family_name), dialect
    )
    if fact is not None:
        if fact.level in (CapabilityLevel.EXPR_CAPABLE, CapabilityLevel.POLYMORPHIC):
            return None  # not a limitation on this dialect
        return fact

    # Legacy fallback (removed by Task 12 once all backends are migrated)
    if backend == "polars":
        from mountainash.expressions.backends.expression_systems.polars.base import (
            PolarsBaseExpressionSystem as B,
        )
    elif backend == "ibis":
        from mountainash.expressions.backends.expression_systems.ibis.base import (
            IbisBaseExpressionSystem as B,
        )
    else:
        from mountainash.expressions.backends.expression_systems.narwhals.base import (
            NarwhalsBaseExpressionSystem as B,
        )
    return B.KNOWN_EXPR_LIMITATIONS.get((function_key, param_name))


def xfail_if_limited(backend: str, function_key: Any, param_name: str, input_type: str):
    """Registry-driven xfail. Dialect-scoped EXPR_CAPABLE refinements make
    the old _NW_POLARS_FIXED allowlist unnecessary: _registry_lookup returns
    None for narwhals-polars where upstream fixed the gap, so no xfail is
    applied and a regression surfaces as an ordinary failure."""
    if input_type in ("raw", "lit"):
        return None

    limitation = _registry_lookup(backend, function_key, param_name)
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
    from expressions.argument_types.conftest import make_df

    df = make_df(op.data, backend)
    arg = _materialize_arg(input_type, op.raw_arg, op.arg_col_name, op.complex_builder)
    expr = op.build(ma.col(op.input_col), arg)
    if op.execution_mode == "over":
        expr = expr.over("__group__")

    limitation = _registry_lookup(backend, op.function_key, op.param_name)

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
