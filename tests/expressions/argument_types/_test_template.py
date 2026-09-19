"""Shared helpers used by every test_arg_types_<category>.py file.

Each per-category file declares:
    TESTED_PARAMS: list[tuple[Any, str]]  # (function_key, param_name)
    OP_SPECS: list[OpSpec]                # one entry per operation under test

Then calls run_argument_matrix(op_spec, backend, input_type) per parametrized case.

Each matrix case builds one bound AST and then materializes it through the
ordinary backend path.  Expectations are owned by the category case itself;
this helper neither reads capability records nor converts native failures into
test outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


import mountainash as ma
from mountainash.expressions import BaseExpressionAPI

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
    expected_by_input: dict[str, list[Any]] | None = None
    """Exact result oracle when this case has backend-neutral value semantics."""


@dataclass(frozen=True)
class BoundMatrixCell:
    """One matrix cell's fully bound AST and matrix argument."""
    expression: BaseExpressionAPI
    node: Any
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
    """Build the exact expression AST for one (op, input_type) matrix cell."""
    arg = _materialize_arg(input_type, op.raw_arg, op.arg_col_name, op.complex_builder)
    receiver = _as_input_expression(arg) if op.matrix_arg_is_input else ma.col(op.input_col)
    expr = op.build(receiver, arg)
    if op.execution_mode == "over":
        expr = expr.over("__group__")
    node = expr.node
    return BoundMatrixCell(expression=expr, node=node, argument=arg)




def _materialize_result(df, compiled, backend: str) -> list[Any]:
    """Execute a compiled result and return its null-preserving values."""
    alias = "__argument_matrix_result__"
    if backend == "polars":
        import polars as pl

        result = df.select(compiled.alias(alias))
        if isinstance(result, pl.LazyFrame):
            result = result.collect()
        return result[alias].to_list()
    if backend in ("ibis", "ibis-polars"):
        return df.select(compiled.name(alias)).to_pyarrow()[alias].to_pylist()
    if backend in ("narwhals-polars", "narwhals-pandas"):
        return df.select(compiled.alias(alias)).to_arrow()[alias].to_pylist()
    raise ValueError(backend)


def run_argument_matrix(op: OpSpec, backend: str, input_type: str) -> None:
    """Execute one case and prove its explicit shape/value contract."""
    from expressions.argument_types.conftest import make_df

    cell = build_matrix_cell(op, input_type)
    df = make_df(op.data, backend)
    result = _materialize_result(df, cell.expression.compile(df), backend)
    receiver_column = op.arg_col_name if op.matrix_arg_is_input else op.input_col
    # Native vector selects return one value for an entirely scalar expression;
    # Ibis table projection broadcasts it across the table instead.
    expected_rows = (
        1 if op.matrix_arg_is_input and input_type in ("raw", "lit") and not backend.startswith("ibis")
        else len(op.data[receiver_column])
    )
    assert len(result) == expected_rows, (
        f"{op.op_name} changed result shape for {input_type} on {backend}: "
        f"{result!r}"
    )
    if op.expected_by_input is not None:
        expected = op.expected_by_input[input_type]
        if op.matrix_arg_is_input and input_type in ("raw", "lit"):
            expected = expected * expected_rows
        assert result == expected, (
            f"{op.op_name} produced the wrong {input_type} result on {backend}: "
            f"{result!r}"
        )
