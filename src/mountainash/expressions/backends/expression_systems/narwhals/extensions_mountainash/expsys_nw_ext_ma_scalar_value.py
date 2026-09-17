"""Narwhals lowering for original-domain value classification."""
from __future__ import annotations

import math
from typing import Any, Callable, Literal, cast

import narwhals as nw
from narwhals._expression_parsing import ExprNode, evaluate_node

from mountainash.core.lazy_imports import import_numpy, import_pandas, import_polars
from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.core.value_classification import ValueKind, boolean_value, text_value, value_kind
from mountainash.expressions.backends.expression_systems.narwhals.base import (
    NarwhalsBaseExpressionSystem,
)
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainAshScalarValueExpressionSystemProtocol,
)


_ObjectProjection = Callable[[object], bool | str | None]


class _ElementwiseBatchExpr(nw.Expr):
    """Preserve Narwhals elementwise metadata for a native batch callback."""

    def __init__(
        self,
        source: nw.Expr,
        callback: Callable[[Any], Any] | None,
        dtype: Any,
        *,
        native_polars: bool,
        tail: tuple[ExprNode, ...] = (),
        name_source: nw.Expr | None = None,
    ) -> None:
        self._source = source
        self._callback = callback
        self._dtype = dtype
        self._native_polars = native_polars
        self._tail = tail
        self._name_source = name_source
        self._nodes = ()

    def _append_node(self, node: ExprNode) -> _ElementwiseBatchExpr:
        return _ElementwiseBatchExpr(
            self._source,
            self._callback,
            self._dtype,
            native_polars=self._native_polars,
            tail=(*self._tail, node),
            name_source=self._name_source,
        )

    def _to_compliant_expr(self, namespace: Any) -> Any:
        source: Any = self._source._to_compliant_expr(namespace)
        if self._callback is None:
            result = source
        elif self._native_polars:
            result = source._with_native(
                source.native.map_batches(
                    self._callback, self._dtype, returns_scalar=False
                )
            )
        else:
            result = source.map_batches(
                self._callback, self._dtype,
                returns_scalar=source._metadata.is_scalar_like,
            )
        if self._name_source is not None:
            # This source is a proven scalar literal plus naming wrappers;
            # its output name depends on no input fields or row evaluation.
            naming: Any = self._name_source._to_compliant_expr(namespace)
            result = result.alias(naming._evaluate_aliases(None)[0])
        result._opt_metadata = source._metadata
        for node in self._tail:
            result = evaluate_node(result, node, namespace)
        return result


def _pandas_elementwise_batches(
    x: nw.Expr, callback: Callable[[Any], Any], dtype: Any
) -> nw.Expr:
    return _ElementwiseBatchExpr(x, callback, dtype, native_polars=False)


def _polars_elementwise_batches(
    x: nw.Expr, callback: Callable[[Any], Any], dtype: Any
) -> nw.Expr:
    return _ElementwiseBatchExpr(x, callback, dtype, native_polars=True)


def _is_pandas_native_nan(value: object, kind: ValueKind) -> bool:
    """Recognize only admitted floating NaNs as Pandas-native absence."""
    if kind is not ValueKind.FLOAT:
        return False
    value_type = type(value)
    if value_type is float:
        return math.isnan(cast("float", value))
    return bool(import_numpy().isnan(value))


def _pandas_object_kind(value: object) -> ValueKind:
    """Classify object storage without dispatching a null predicate to objects."""
    kind = value_kind(value)
    if _is_pandas_native_nan(value, kind):
        return ValueKind.ABSENT
    return kind


def _pandas_kind_projection(value: object) -> str:
    return _pandas_object_kind(value).value


def _pandas_boolean_projection(source: str) -> _ObjectProjection:
    def project(value: object) -> bool | None:
        if _pandas_object_kind(value) is ValueKind.ABSENT:
            return None
        return boolean_value(value, source=source)

    return project


def _pandas_text_projection(value: object) -> str | None:
    if _pandas_object_kind(value) is ValueKind.ABSENT:
        return None
    return text_value(value)


def _polars_kind_projection(value: object) -> str:
    return value_kind(value).value


def _polars_boolean_projection(source: str) -> _ObjectProjection:
    return lambda value: boolean_value(value, source=source)


def _polars_text_projection(value: object) -> str | None:
    return text_value(value)


def _pandas_object_projection(
    series: Any,
    projection: _ObjectProjection,
    *,
    dtype: str,
) -> Any:
    """Apply one object projection while preserving the original Pandas index."""
    native = series.native
    pandas = import_pandas()
    output = transit_call(
        BoundaryKey.EXPRESSION_NARWHALS_OBJECT_NATIVE_CALLBACK,
        pandas.Series,
        pandas.array([projection(value) for value in native], dtype=dtype),
        index=native.index,
        name=native.name,
        trace_source=series,
    )
    return series._with_native(output)


def _polars_object_projection(
    series: Any,
    projection: _ObjectProjection,
    *,
    dtype: Any,
) -> Any:
    """Apply one object projection through the native Polars batch callback."""
    polars = import_polars()
    return polars.Series(
        series.name,
        [projection(series[index]) for index in range(len(series))],
        dtype=dtype,
    )


def _pandas_typed_null_projection(series: Any, *, dtype: str) -> Any:
    """Build one nullable Pandas output without examining input values."""
    native = series.native
    pandas = import_pandas()
    output = transit_call(
        BoundaryKey.EXPRESSION_NARWHALS_PANDAS_TYPED_CALLBACK,
        pandas.Series,
        pandas.array([pandas.NA] * len(native), dtype=dtype),
        index=native.index,
        name=native.name,
        trace_source=series,
    )
    return series._with_native(output)


def _pandas_typed_binary_projection(series: Any) -> Any:
    """Project native numeric zero and one with masks into BooleanArray."""
    native = series.native
    pandas = import_pandas()
    output = transit_call(
        BoundaryKey.EXPRESSION_NARWHALS_PANDAS_TYPED_CALLBACK,
        pandas.Series,
        pandas.array([pandas.NA] * len(native), dtype="boolean"),
        index=native.index,
        name=native.name,
        trace_source=series,
    )
    zero = native.eq(0).fillna(False)
    one = native.eq(1).fillna(False)
    return series._with_native(output.mask(zero, False).mask(one, True))


def _pandas_typed_integer_finite_projection(series: Any) -> Any:
    """Project native integer zero/nonzero values into BooleanArray."""
    native = series.native
    pandas = import_pandas()
    output = transit_call(
        BoundaryKey.EXPRESSION_NARWHALS_PANDAS_TYPED_CALLBACK,
        pandas.Series,
        pandas.array([pandas.NA] * len(native), dtype="boolean"),
        index=native.index,
        name=native.name,
        trace_source=series,
    )
    zero = native.eq(0).fillna(False)
    nonzero = native.ne(0).fillna(False)
    return series._with_native(output.mask(zero, False).mask(nonzero, True))


def _pandas_typed_float_finite_projection(series: Any) -> Any:
    """Project finite native floats while retaining null and NaN distinctions."""
    native = series.native
    pandas = import_pandas()
    output = transit_call(
        BoundaryKey.EXPRESSION_NARWHALS_PANDAS_TYPED_CALLBACK,
        pandas.Series,
        pandas.array([pandas.NA] * len(native), dtype="boolean"),
        index=native.index,
        name=native.name,
        trace_source=series,
    )
    finite = (
        native.notna()
        & native.eq(native).fillna(False)
        & native.ne(float("inf")).fillna(False)
        & native.ne(float("-inf")).fillna(False)
    )
    zero = (finite & native.eq(0).fillna(False)).fillna(False)
    nonzero = (finite & native.ne(0).fillna(False)).fillna(False)
    return series._with_native(output.mask(zero, False).mask(nonzero, True))


class MountainAshNarwhalsScalarValueExpressionSystem(
    NarwhalsBaseExpressionSystem,
    MountainAshScalarValueExpressionSystemProtocol[nw.Expr],
):
    """Narwhals implementation of value-domain classification and projections."""

    def value_kind(self, x: nw.Expr, /) -> nw.Expr:
        descriptor = self.operand_type("x")
        if descriptor.storage_kind == "pandas_object":
            return _pandas_elementwise_batches(
                x,
                lambda series: _pandas_object_projection(
                    series, _pandas_kind_projection, dtype="string"
                ),
                nw.String,
            )
        if descriptor.storage_kind == "polars_object":
            return _polars_elementwise_batches(
                x,
                lambda series: _polars_object_projection(
                    series, _polars_kind_projection, dtype=import_polars().String
                ),
                import_polars().String,
            )

        label = {
            "boolean": ValueKind.BOOLEAN.value,
            "integer": ValueKind.INTEGER.value,
            "float": ValueKind.FLOAT.value,
            "text": ValueKind.TEXT.value,
            "null": ValueKind.ABSENT.value,
        }.get(descriptor.logical_kind, ValueKind.UNSUPPORTED.value)
        return (
            nw.when(x.is_null())
            .then(nw.lit(ValueKind.ABSENT.value, dtype=nw.String))
            .otherwise(nw.lit(label, dtype=nw.String))
        )

    def boolean_value(
        self,
        x: nw.Expr,
        /,
        *,
        source: Literal["boolean", "binary_number", "finite_number"] = "boolean",
    ) -> nw.Expr:
        descriptor = self.operand_type("x")
        if descriptor.storage_kind == "pandas_object":
            return _pandas_elementwise_batches(
                x,
                lambda series: _pandas_object_projection(
                    series, _pandas_boolean_projection(source), dtype="boolean"
                ),
                nw.Boolean,
            )
        if descriptor.storage_kind == "polars_object":
            return _polars_elementwise_batches(
                x,
                lambda series: _polars_object_projection(
                    series,
                    _polars_boolean_projection(source),
                    dtype=import_polars().Boolean,
                ),
                import_polars().Boolean,
            )
        if source == "boolean" and descriptor.logical_kind == "boolean":
            return x

        pandas_typed = descriptor.storage_kind in {
            "pandas_numpy", "pandas_nullable", "pandas_arrow"
        }
        if source == "binary_number" and descriptor.logical_kind in {"integer", "float"}:
            if pandas_typed:
                return _pandas_elementwise_batches(
                    x, _pandas_typed_binary_projection, nw.Boolean
                )
            null_boolean = nw.lit(None, dtype=nw.Boolean)
            return (
                nw.when(x.is_null())
                .then(null_boolean)
                .when(x == 0)
                .then(nw.lit(False, dtype=nw.Boolean))
                .when(x == 1)
                .then(nw.lit(True, dtype=nw.Boolean))
                .otherwise(null_boolean)
            )
        if source == "finite_number" and descriptor.logical_kind == "integer":
            if pandas_typed:
                return _pandas_elementwise_batches(
                    x, _pandas_typed_integer_finite_projection, nw.Boolean
                )
            null_boolean = nw.lit(None, dtype=nw.Boolean)
            return nw.when(x.is_null()).then(null_boolean).otherwise(x != 0)
        if source == "finite_number" and descriptor.logical_kind == "float":
            if pandas_typed:
                return _pandas_elementwise_batches(
                    x, _pandas_typed_float_finite_projection, nw.Boolean
                )
            null_boolean = nw.lit(None, dtype=nw.Boolean)
            return (
                nw.when(x.is_null())
                .then(null_boolean)
                .when(x.is_finite())
                .then(x != 0)
                .otherwise(null_boolean)
            )
        if pandas_typed:
            return _pandas_elementwise_batches(
                x,
                lambda series: _pandas_typed_null_projection(series, dtype="boolean"),
                nw.Boolean,
            )
        null_boolean = nw.lit(None, dtype=nw.Boolean)
        return nw.when(x.is_null()).then(null_boolean).otherwise(null_boolean)

    def text_value(self, x: nw.Expr, /) -> nw.Expr:
        descriptor = self.operand_type("x")
        if descriptor.storage_kind == "pandas_object":
            return _pandas_elementwise_batches(
                x,
                lambda series: _pandas_object_projection(
                    series, _pandas_text_projection, dtype="string"
                ),
                nw.String,
            )
        if descriptor.storage_kind == "polars_object":
            return _polars_elementwise_batches(
                x,
                lambda series: _polars_object_projection(
                    series, _polars_text_projection, dtype=import_polars().String
                ),
                import_polars().String,
            )
        if descriptor.logical_kind == "text":
            return x
        if descriptor.storage_kind in {
            "pandas_numpy", "pandas_nullable", "pandas_arrow"
        }:
            return _pandas_elementwise_batches(
                x,
                lambda series: _pandas_typed_null_projection(series, dtype="string"),
                nw.String,
            )
        null_text = nw.lit(None, dtype=nw.String)
        return nw.when(x.is_null()).then(null_text).otherwise(null_text)
