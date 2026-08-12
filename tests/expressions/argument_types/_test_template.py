"""Shared helpers used by every test_arg_types_<category>.py file.

Each per-category file declares:
    TESTED_PARAMS: list[tuple[Any, str]]  # (function_key, param_name)
    OP_SPECS: list[OpSpec]                # one entry per operation under test

Then calls run_argument_matrix(op_spec, backend, input_type) per parametrized case.

Every cell's expectation and execution build from ONE bound AST — build_matrix_cell()
— so xfail_if_limited() (collection time) and run_argument_matrix() (execution time)
can never diverge. See backlog arg-matrix-xfail-blind-to-value-class-facts and spec
2026-08-09-argument-matrix-value-class-facts-design.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import pytest

import mountainash as ma
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import CapabilityLevel, WILDCARD_PARAM
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import (
    ScalarFunctionNode,
)
from tests.fixtures.capability_gating import build_gate_fact, first_scalar_build_gate

from expressions.argument_types.conftest import matrix_identity

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
    matrix_arg_is_input: bool = False
    """When True, the materialized matrix argument (not op.input_col) becomes
    the receiver `op.build` is called on — for ops whose only expression-typed
    argument is the receiver itself (e.g. to_timezone.x), so raw/lit/col/complex
    genuinely vary the bound call rather than an ignored placeholder."""


@dataclass(frozen=True)
class BoundMatrixCell:
    """One matrix cell's fully bound AST — the single source of truth both
    expectation derivation and execution consult."""
    expression: BaseExpressionAPI
    node: Any
    operation_key: Any
    argument: Any


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


def _as_input_expression(value: Any) -> BaseExpressionAPI:
    return value if isinstance(value, BaseExpressionAPI) else ma.lit(value)


def build_matrix_cell(op: OpSpec, input_type: str) -> BoundMatrixCell:
    """Build the exact expression AST for one (op, input_type) matrix cell.

    The ONLY place that constructs a matrix cell's expression — both
    xfail_if_limited (expectation) and run_argument_matrix (execution) call
    this, so their builds are always structurally identical.
    """
    arg = _materialize_arg(input_type, op.raw_arg, op.arg_col_name, op.complex_builder)
    receiver = _as_input_expression(arg) if op.matrix_arg_is_input else ma.col(op.input_col)
    expr = op.build(receiver, arg)
    if op.execution_mode == "over":
        expr = expr.over("__group__")
    node = expr.node
    return BoundMatrixCell(
        expression=expr, node=node, operation_key=node.function_key, argument=arg
    )


def _legacy_argument_gate(operation_key: Any, identity, param_name: str):
    """Pre-item-71 argument-only lookup, preserved exactly for non-scalar nodes
    (window functions have no production option-gating equivalent to mirror)."""
    fact = CapabilityRegistry.capability_for(
        operation_key, param_name, identity.family, identity.dialect
    )
    if fact is None or fact.level in (CapabilityLevel.EXPR_CAPABLE, CapabilityLevel.POLYMORPHIC):
        return None
    return fact


def _cell_limitation(cell: BoundMatrixCell, op: OpSpec, identity, input_type: str):
    """(limitation, wildcard_residue) for one bound cell.

    Scalar cells: limitation is the spine-derived build-time gate across the
    WHOLE emitted AST (op-wide -> arguments -> options, first_scalar_build_gate);
    residue is consulted only as a later materialize-time fallback.

    Non-scalar cells: the pre-item-71 precedence is preserved exactly — a
    wildcard residue fact short-circuits before any per-argument lookup runs.
    """
    residue = CapabilityRegistry.residue_for(identity.family, identity.dialect)
    wildcard_residue = residue.get((cell.operation_key, WILDCARD_PARAM))

    if isinstance(cell.node, ScalarFunctionNode):
        limitation = first_scalar_build_gate(cell.node, identity)
    elif wildcard_residue is None and input_type not in ("raw", "lit"):
        limitation = _legacy_argument_gate(cell.operation_key, identity, op.param_name)
    else:
        limitation = None
    return limitation, wildcard_residue


def xfail_if_limited(backend: str, op: OpSpec, input_type: str):
    """Spine-derived xfail, keyed off the exact bound AST for this cell.

    Scalar operations: build-time gate first (whole emitted AST), residue
    fallback second. Non-scalar operations: residue-first, matching the
    pre-item-71 behavior unchanged (no production option-gating equivalent).
    """
    identity = matrix_identity(backend)
    cell = build_matrix_cell(op, input_type)
    limitation, wildcard_residue = _cell_limitation(cell, op, identity, input_type)

    if isinstance(cell.node, ScalarFunctionNode):
        fact = limitation if limitation is not None else wildcard_residue
    else:
        fact = wildcard_residue if wildcard_residue is not None else limitation

    if fact is None:
        return None
    return pytest.mark.xfail(
        strict=True,
        raises=BackendCapabilityError,
        reason=fact.message,
    )


def _materialize_result(df, compiled, backend: str) -> None:
    """Force execution to surface errors that fire at materialization time."""
    if backend == "polars":
        import polars as pl

        if isinstance(df, pl.LazyFrame):
            df.select(compiled).collect()
        else:
            df.select(compiled)
    elif backend in ("ibis", "ibis-polars"):
        df.select(compiled.name("__result__")).execute()
    elif backend in ("narwhals-polars", "narwhals-pandas"):
        df.select(compiled).to_native()
    else:
        raise ValueError(backend)


def run_argument_matrix(op: OpSpec, backend: str, input_type: str):
    """Execute one cell of the (operation × backend × input_type) matrix."""
    from expressions.argument_types.conftest import make_df

    identity = matrix_identity(backend)
    cell = build_matrix_cell(op, input_type)
    limitation, wildcard_residue = _cell_limitation(cell, op, identity, input_type)
    df = make_df(op.data, backend)

    try:
        compiled = cell.expression.compile(df)
        assert compiled is not None
        _materialize_result(df, compiled, backend)
    except BackendCapabilityError:
        raise
    except Exception as e:
        for fact in (limitation, wildcard_residue):
            if fact is not None and fact.native_errors and isinstance(e, fact.native_errors):
                raise BackendCapabilityError(
                    str(fact.message),
                    backend=backend,
                    function_key=cell.operation_key,
                    limitation=fact,
                ) from e
        raise
