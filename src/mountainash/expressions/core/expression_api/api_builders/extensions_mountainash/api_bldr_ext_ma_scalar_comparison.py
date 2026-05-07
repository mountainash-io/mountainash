"""Mountainash extension comparison operations APIBuilder.

Polars-compatible aliases for standard comparison operations.
Standard comparison operations are handled by SubstraitScalarComparisonAPIBuilder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarComparisonAPIBuilderProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_COMPARISON,
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, IfThenNode, LiteralNode


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarComparisonAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarComparisonAPIBuilderProtocol):
    """Mountainash extension comparison operations.

    Provides Polars-compatible aliases for standard comparison operations.
    Standard comparison operations live in SubstraitScalarComparisonAPIBuilder.
    """

    # Short aliases for Substrait comparison operations

    def eq(self, other) -> BaseExpressionAPI:
        """Alias for equal()."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def ne(self, other) -> BaseExpressionAPI:
        """Alias for not_equal()."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.NOT_EQUAL,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def ge(self, other) -> BaseExpressionAPI:
        """Alias for gte()."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GTE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def le(self, other) -> BaseExpressionAPI:
        """Alias for lte()."""
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    # Polars-compatible aliases

    def is_between(self, low, high, closed: str = "both") -> BaseExpressionAPI:
        """Alias for between() — Polars compatibility."""
        low_node = self._to_substrait_node(low)
        high_node = self._to_substrait_node(high)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN,
            arguments=[self._node, low_node, high_node],
            options={"closed": closed},
        )
        return self._build(node)

    # Convenience methods (AST-level composition, no backend work needed)

    def is_not_nan(self) -> BaseExpressionAPI:
        """Whether value is not NaN. Equivalent to not_(is_nan())."""
        is_nan_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN,
            arguments=[self._node],
        )
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT,
            arguments=[is_nan_node],
        )
        return self._build(node)

    def clip(self, lower=None, upper=None) -> BaseExpressionAPI:
        """Clip values to a range. Values below lower become lower, above upper become upper.

        Args:
            lower: Minimum value. None means no lower bound.
            upper: Maximum value. None means no upper bound.
        """
        if lower is None and upper is None:
            return self._build(self._node)

        conditions = []
        if lower is not None:
            lower_node = self._to_substrait_node(lower)
            lt_cond = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT,
                arguments=[self._node, lower_node],
            )
            conditions.append((lt_cond, lower_node))

        if upper is not None:
            upper_node = self._to_substrait_node(upper)
            gt_cond = ScalarFunctionNode(
                function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,
                arguments=[self._node, upper_node],
            )
            conditions.append((gt_cond, upper_node))

        node = IfThenNode(
            conditions=conditions,
            else_clause=self._node,
        )
        return self._build(node)

    # Null-safe comparison (AST-level composition)

    def eq_missing(self, other) -> BaseExpressionAPI:
        """Null-safe equality: None == None returns True.

        Equivalent to Polars eq_missing() or SQL IS NOT DISTINCT FROM.
        """
        other_node = self._to_substrait_node(other)
        # (self == other) OR (self.is_null AND other.is_null)
        eq_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL,
            arguments=[self._node, other_node],
        )
        self_null = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL,
            arguments=[self._node],
        )
        other_null = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL,
            arguments=[other_node],
        )
        both_null = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND,
            arguments=[self_null, other_null],
        )
        result = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR,
            arguments=[eq_node, both_null],
        )
        return self._build(result)

    def ne_missing(self, other) -> BaseExpressionAPI:
        """Null-safe inequality: None == None returns False.

        Equivalent to Polars ne_missing() or SQL IS DISTINCT FROM.
        """
        other_node = self._to_substrait_node(other)
        # NOT((self == other) OR (self.is_null AND other.is_null))
        eq_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL,
            arguments=[self._node, other_node],
        )
        self_null = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL,
            arguments=[self._node],
        )
        other_null = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL,
            arguments=[other_node],
        )
        both_null = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND,
            arguments=[self_null, other_null],
        )
        eq_missing = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR,
            arguments=[eq_node, both_null],
        )
        result = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT,
            arguments=[eq_missing],
        )
        return self._build(result)

    def null_count(self) -> BaseExpressionAPI:
        """Count of null values. Equivalent to is_null().sum()."""
        is_null_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL,
            arguments=[self._node],
        )
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM,
            arguments=[is_null_node],
        )
        return self._build(node)

    def has_nulls(self) -> BaseExpressionAPI:
        """Whether any values are null. Equivalent to is_null().sum().gt(0)."""
        is_null_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL,
            arguments=[self._node],
        )
        sum_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM,
            arguments=[is_null_node],
        )
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,
            arguments=[sum_node, LiteralNode(value=0)],
        )
        return self._build(node)

    def is_close(self, other, abs_tol: float = 1e-8, rel_tol: float = 1e-5) -> BaseExpressionAPI:
        """Whether two values are approximately equal.

        Uses: abs(self - other) <= abs_tol + rel_tol * abs(other)

        Args:
            other: Value to compare against.
            abs_tol: Absolute tolerance.
            rel_tol: Relative tolerance.
        """
        other_node = self._to_substrait_node(other)
        # abs(self - other)
        diff = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
            arguments=[self._node, other_node],
        )
        abs_diff = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
            arguments=[diff],
        )
        # abs_tol + rel_tol * abs(other)
        abs_other = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
            arguments=[other_node],
        )
        rel_part = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            arguments=[LiteralNode(value=rel_tol), abs_other],
        )
        threshold = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            arguments=[LiteralNode(value=abs_tol), rel_part],
        )
        # abs_diff <= threshold
        result = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE,
            arguments=[abs_diff, threshold],
        )
        return self._build(result)
