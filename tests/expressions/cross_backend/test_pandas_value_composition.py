"""Pandas storage regressions for bounded value compositions."""
from __future__ import annotations

import narwhals as nw
import numpy as np
import pandas as pd
import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.dtypes.metadata import OperandType
from mountainash.expressions.backends.expression_systems.narwhals import (
    NarwhalsExpressionSystem,
)
from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
from mountainash.expressions.core.expression_nodes.substrait.exn_literal import LiteralNode
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


def _select(frame: pd.DataFrame, expression: ma.BaseExpressionAPI) -> pd.Series:
    selected = nw.from_native(frame).select(expression.compile(frame).alias("value"))
    return selected.to_native()["value"]


def test_leading_null_coalesce_keeps_pandas_row_shape() -> None:
    """A scalar null must not truncate a typed Pandas coalesce projection."""
    frame = pd.DataFrame({"value": pd.Series([True, False], dtype=bool)})

    result = _select(
        frame,
        ma.coalesce(ma.lit(None), ma.col("value")).boolean_value(),
    )

    assert result.tolist() == [True, False]
    assert str(result.dtype) == "bool"


def test_conditional_null_branch_uses_nullable_boolean_storage() -> None:
    """A possible null branch preserves Boolean semantics instead of object storage."""
    frame = pd.DataFrame(
        {
            "condition": pd.Series([True, False], dtype=bool),
            "value": pd.Series([True, False], dtype=bool),
        }
    )
    expression = (
        ma.when(ma.col("condition"))
        .then(ma.col("value"))
        .otherwise(ma.lit(None))
    )
    visitor = UnifiedExpressionVisitor(
        NarwhalsExpressionSystem(dialect="narwhals-pandas"), input_data=frame
    )

    with visitor.input_scope(frame):
        assert visitor.type_context.resolve_native(expression.node).descriptor == OperandType(
            "boolean", "pandas_nullable", True
        )

    result = _select(frame, expression.boolean_value())

    assert bool(result.iloc[0]) is True
    assert result.isna().tolist() == [False, True]
    assert str(result.dtype) == "boolean"


def test_conditional_uint64_null_preserves_finite_number() -> None:
    """Null conditional branches must not float-promote the UInt64 maximum."""
    maximum = np.iinfo(np.uint64).max
    frame = pd.DataFrame(
        {
            "condition": pd.Series([True, False], dtype=bool),
            "value": pd.Series([maximum, 0], dtype=np.uint64),
        }
    )
    expression = (
        ma.when(ma.col("condition"))
        .then(ma.col("value"))
        .otherwise(ma.lit(None))
        .boolean_value(source="finite_number")
    )

    result = _select(frame, expression)

    assert bool(result.iloc[0]) is True
    assert result.isna().tolist() == [False, True]
    assert str(result.dtype) == "boolean"



def test_explicit_typed_null_literal_remains_nullable_boolean() -> None:
    """Declared literal metadata and Narwhals lowering must agree on null."""
    frame = pd.DataFrame({"value": pd.Series([True], dtype=bool)})
    expression = BaseExpressionAPI(LiteralNode(value=None, dtype=D.BOOL))
    visitor = UnifiedExpressionVisitor(
        NarwhalsExpressionSystem(dialect="narwhals-pandas"), input_data=frame
    )

    with visitor.input_scope(frame):
        assert visitor.type_context.resolve_native(expression.node).descriptor == OperandType(
            "boolean", "pandas_nullable", True
        )

    result = _select(frame, expression)

    assert result.isna().tolist() == [True]
    assert str(result.dtype) == "boolean"


def test_conditional_nullable_boolean_branch_keeps_selected_null() -> None:
    """Mixed NumPy/nullable Boolean branches must not become object storage."""
    frame = pd.DataFrame(
        {
            "condition": pd.Series([True, False], dtype=bool),
            "numpy": pd.Series([True, False], dtype=bool),
            "nullable": pd.Series([False, pd.NA], dtype="boolean"),
        }
    )
    expression = (
        ma.when(ma.col("condition"))
        .then(ma.col("numpy"))
        .otherwise(ma.col("nullable"))
        .boolean_value()
    )

    result = _select(frame, expression)

    assert bool(result.iloc[0]) is True
    assert result.isna().tolist() == [False, True]
    assert str(result.dtype) == "boolean"


@pytest.mark.parametrize(
    "failure,last",
    [(ma.CaseFailureBehaviour.NULL, "bad"), (ma.CaseFailureBehaviour.THROW, None)],
)
def test_parser_projection_preserves_boolean_inversion(failure, last) -> None:
    frame = pd.DataFrame({"value": pd.Series(["true", "false", last], dtype="string")})
    expression = ma.col("value").parse_boolean(
        true_values=("true",), false_values=("false",), field_name="value",
        failure_behavior=failure
    ).boolean_value()
    result = _select(frame, ~expression)
    assert result.tolist()[:2] == [False, True]
    assert result.isna().tolist() == [False, False, True]
    assert pd.api.types.is_bool_dtype(result.dtype)


@pytest.mark.parametrize("null_first", [False, True])
def test_aliased_null_conditional_preserves_uint64_cast(null_first) -> None:
    frame = pd.DataFrame({
        "condition": [True, False],
        "value": pd.Series([np.iinfo(np.uint64).max] * 2, dtype=np.uint64),
    })
    missing = ma.lit(None).name.alias("missing")
    value = ma.col("value")
    expression = (
        ma.when(ma.col("condition"))
        .then(missing if null_first else value)
        .otherwise(value if null_first else missing)
        .cast(D.U64).boolean_value(source="finite_number")
    )
    result = _select(frame, expression)
    assert bool(result.iloc[1 if null_first else 0]) is True
    assert result.isna().tolist() == ([True, False] if null_first else [False, True])


@pytest.mark.parametrize("missing", [pd.NA, pd.NaT, None])
def test_wrapped_null_coalesce_preserves_rows_and_name(missing) -> None:
    frame = pd.DataFrame({"value": pd.Series([True, False], dtype=bool)})
    expression = ma.coalesce(
        ma.lit(missing).name.alias("missing"), ma.col("value")
    ).boolean_value()
    result = nw.from_native(frame).select(expression.compile(frame)).to_native()
    assert result.columns.tolist() == ["missing"]
    assert result["missing"].tolist() == [True, False]


@pytest.mark.parametrize("composition", ["conditional", "coalesce"])
def test_nullable_integer_widths_have_lossless_common_carrier(composition) -> None:
    frame = pd.DataFrame({
        "condition": [True, False],
        "small": pd.Series([1, None], dtype="Int8"),
        "large": pd.Series([256, 256], dtype="Int64"),
    })
    expression = (
        ma.when(ma.col("condition")).then(ma.col("small")).otherwise(ma.col("large"))
        if composition == "conditional"
        else ma.coalesce(ma.col("small"), ma.col("large"))
    )
    result = _select(frame, expression.boolean_value(source="binary_number"))
    assert bool(result.iloc[0]) is True
    assert result.isna().tolist() == [False, True]
    assert pd.api.types.is_bool_dtype(result.dtype)


@pytest.mark.parametrize("composition", ["conditional", "coalesce"])
@pytest.mark.parametrize("arrow", [False, True])
def test_floating_common_carrier_preserves_tiny_nonzero(composition, arrow) -> None:
    dtype = "double[pyarrow]" if arrow else "Float64"
    frame = pd.DataFrame({
        "condition": [False, False],
        "small": pd.Series([None, None], dtype="Float32"),
        "large": pd.Series([1e-50, 0.0], dtype=dtype),
    })
    expression = (
        ma.when(ma.col("condition")).then(ma.col("small")).otherwise(ma.col("large"))
        if composition == "conditional"
        else ma.coalesce(ma.col("small"), ma.col("large"))
    )
    result = _select(frame, expression.boolean_value(source="finite_number"))
    assert result.tolist() == [True, False]


def test_common_arrow_float_preserves_concrete_nan_validity() -> None:
    import pyarrow as pa

    values = pd.arrays.ArrowExtensionArray(pa.array([float("nan"), None], type=pa.float64()))
    frame = pd.DataFrame({
        "small": pd.Series([None, None], dtype="Float32"),
        "large": pd.Series(values),
    })
    expression = ma.coalesce(ma.col("small"), ma.col("large")).value_kind()
    assert _select(frame, expression).tolist() == ["float", "absent"]


def test_aliased_float_literal_retains_native_width() -> None:
    frame = pd.DataFrame({
        "condition": [True, False],
        "value": pd.Series([0.0, 0.0], dtype="Float32"),
    })
    expression = (
        ma.when(ma.col("condition"))
        .then(ma.lit(1e-50).name.alias("tiny"))
        .otherwise(ma.col("value"))
        .boolean_value(source="finite_number")
    )
    assert _select(frame, expression).tolist() == [True, False]