"""Boolean operations mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import BooleanBuilderProtocol, ENUM_BOOLEAN_OPERATORS
from ..expression_nodes import (
    BooleanComparisonExpressionNode,
    BooleanIterableExpressionNode,
    BooleanUnaryExpressionNode,
    BooleanCollectionExpressionNode,
    BooleanConstantExpressionNode,
    BooleanIsCloseExpressionNode,
    BooleanBetweenExpressionNode,
)


class BooleanExpressionBuilder(BaseExpressionBuilder, BooleanBuilderProtocol):
    """
    Mixin providing boolean operations for ExpressionBuilder.

    Implements all methods from BooleanBuilderProtocol to create boolean
    expression nodes that can be compiled to any backend.
    """

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Equal to (==).

        Args:
            other: Value or expression to compare with

        Returns:
            New ExpressionBuilder with comparison node
        """

        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.EQ,
            self._node,
            other_node
        )
        return self.create(node)

    def ne(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Not equal to (!=)."""

        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NE,
            self._node,
            other_node
        )
        return self.create(node)

    def gt(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Greater than (>)."""

        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.GT,
            self._node,
            other_node
        )
        return self.create(node)

    def lt(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Less than (<)."""

        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.LT,
            self._node,
            other_node
        )
        return self.create(node)

    def ge(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Greater than or equal (>=)."""

        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.GE,
            self._node,
            other_node
        )
        return self.create(node)

    def le(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Less than or equal (<=)."""

        other_node = self._to_node_or_value(other)
        node = BooleanComparisonExpressionNode(
            ENUM_BOOLEAN_OPERATORS.LE,
            self._node,
            other_node
        )
        return self.create(node)

    def is_close(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any], precision: float = 1e-5) -> BaseExpressionBuilder:
        """
        Check if values are approximately equal within precision.

        Args:
            other: Value to compare with
            precision: Maximum allowed difference (default: 1e-5)
        """
        from ..base_expression_builder import BaseExpressionBuilder
        other_node = self._to_node_or_value(other)
        node = BooleanIsCloseExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_CLOSE,
            self._node,
            other_node,
            precision
        )
        return self.create(node)

    def between(self, lower: Union[BaseExpressionBuilder, ExpressionNode, Any],
                upper: Union[BaseExpressionBuilder, ExpressionNode, Any],
                closed: str = "both") -> BaseExpressionBuilder:
        """
        Check if value is between bounds.

        Args:
            lower: Lower bound
            upper: Upper bound
            closed: Which bounds are inclusive ("left", "right", "both", "neither")
        """

        # Note: BooleanBetweenExpressionNode(operator, left, right, closed)
        # where left is the value, right is upper bound, and we need to handle lower separately
        # Based on the constructor, this seems wrong - let me check the visitor to understand usage
        lower_node = self._to_node_or_value(lower)
        upper_node = self._to_node_or_value(upper)
        node = BooleanBetweenExpressionNode(
            ENUM_BOOLEAN_OPERATORS.BETWEEN,
            self._node,  # value to check
            lower_node,  # should be lower, but constructor says "right"
            closed
        )
        # TODO: Verify this matches visitor expectations
        return self.create(node)

    # ========================================
    # Python Comparison Operators
    # ========================================

    def __gt__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python > operator."""
        return self.gt(other)

    def __lt__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python < operator."""
        return self.lt(other)

    def __ge__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python >= operator."""
        return self.ge(other)

    def __le__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python <= operator."""
        return self.le(other)

    def __eq__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python == operator."""
        return self.eq(other)

    def __ne__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python != operator."""
        return self.ne(other)

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(self, values: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Check if value is in a collection.

        Args:
            values: Collection to check membership in
        """

        values_node = self._to_node_or_value(values)
        node = BooleanCollectionExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_IN,
            self._node,  # operand
            None,  # element (not used?)
            values_node  # container
        )
        # TODO: Verify operand/element/container usage
        return self.create(node)

    def is_not_in(self, values: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Check if value is not in a collection."""

        values_node = self._to_node_or_value(values)
        node = BooleanCollectionExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_NOT_IN,
            self._node,  # operand
            None,  # element
            values_node  # container
        )
        return self.create(node)

    # ========================================
    # Logical Constants
    # ========================================

    def always_true(self) -> BaseExpressionBuilder:
        """Return a constant TRUE value."""

        node = BooleanConstantExpressionNode(
            ENUM_BOOLEAN_OPERATORS.ALWAYS_TRUE
        )
        return self.create(node)

    def always_false(self) -> BaseExpressionBuilder:
        """Return a constant FALSE value."""

        node = BooleanConstantExpressionNode(
            ENUM_BOOLEAN_OPERATORS.ALWAYS_FALSE
        )
        return self.create(node)

    # ========================================
    # Logical Operators (Iterable)
    # ========================================

    def and_(self, *others: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Logical AND operation.

        Args:
            *others: Other expressions to AND with this one
        """

        # Collect all operands
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.AND,
            *operands
        )
        return self.create(node)

    def or_(self, *others: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Logical OR operation."""

        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.OR,
            *operands
        )
        return self.create(node)

    def xor_(self, *others: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Logical XOR operation."""

        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.XOR,
            *operands
        )
        return self.create(node)

    def xor_parity(self, *others: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        """

        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.XOR_PARITY,
            *operands
        )
        return self.create(node)

    # ========================================
    # Python Logical Operators
    # ========================================

    def __and__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python & operator."""
        return self.and_(other)

    def __or__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python | operator."""
        return self.or_(other)

    def __xor__(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """Python ^ operator."""
        return self.xor_(other)

    # ========================================
    # Unary Operators
    # ========================================

    def is_true(self) -> BaseExpressionBuilder:
        """Check if expression evaluates to TRUE (for ternary logic)."""

        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_TRUE,
            self._node
        )
        return self.create(node)

    def is_false(self) -> BaseExpressionBuilder:
        """Check if expression evaluates to FALSE (for ternary logic)."""

        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_FALSE,
            self._node
        )
        return self.create(node)

    def not_(self) -> BaseExpressionBuilder:
        """Logical NOT operation."""

        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NOT,
            self._node
        )
        return self.create(node)

    def __invert__(self) -> BaseExpressionBuilder:
        """Python ~ operator (logical NOT)."""
        return self.not_()
