"""Arithmetic operations mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import ArithmeticBuilderProtocol, ENUM_ARITHMETIC_OPERATORS
from ..expression_nodes import (
    ArithmeticExpressionNode,
    ArithmeticIterableExpressionNode,
)


class ArithmeticExpressionBuilder(BaseExpressionBuilder, ArithmeticBuilderProtocol):
    """
    Mixin providing arithmetic operations for ExpressionBuilder.

    Implements all methods from ArithmeticBuilderProtocol to create arithmetic
    expression nodes that can be compiled to any backend.

    Arithmetic operations:
    - Binary: subtract, divide, modulo, power, floor_divide
    - N-ary: add, multiply (can chain multiple operands)
    - Python operators: +, -, *, /, %, **, //
    - Reverse operators: __radd__, __rsub__, etc.
    """


    # ========================================
    # Binary Arithmetic Operations
    # ========================================

    def subtract(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Subtraction (-).

        Args:
            other: Value or expression to subtract

        Returns:
            New ExpressionBuilder with subtraction node
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.SUBTRACT,
            self._node,
            other_node
        )
        return self.create(node)

    def divide(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Division (/).

        Args:
            other: Value or expression to divide by

        Returns:
            New ExpressionBuilder with division node
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.DIVIDE,
            self._node,
            other_node
        )
        return self.create(node)

    def modulo(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Modulo (%).

        Args:
            other: Value or expression for modulo operation

        Returns:
            New ExpressionBuilder with modulo node
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.MODULO,
            self._node,
            other_node
        )
        return self.create(node)

    def power(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Exponentiation (**).

        Args:
            other: Exponent value or expression

        Returns:
            New ExpressionBuilder with power node
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.POWER,
            self._node,
            other_node
        )
        return self.create(node)

    def floor_divide(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Floor division (//).

        Args:
            other: Value or expression to divide by

        Returns:
            New ExpressionBuilder with floor division node
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.FLOOR_DIVIDE,
            self._node,
            other_node
        )
        return self.create(node)

    # ========================================
    # N-ary Arithmetic Operations (Iterable)
    # ========================================

    def add(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Addition (+).

        Can be chained with multiple operands.

        Args:
            other: Value or expression to add

        Returns:
            New ExpressionBuilder with addition node
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticIterableExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.ADD,
            self._node,
            other_node
        )
        return self.create(node)

    def multiply(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Multiplication (*).

        Can be chained with multiple operands.

        Args:
            other: Value or expression to multiply by

        Returns:
            New ExpressionBuilder with multiplication node
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticIterableExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.MULTIPLY,
            self._node,
            other_node
        )
        return self.create(node)

    # ========================================
    # Python Arithmetic Operators
    # ========================================

    def __add__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """Python + operator."""
        return self.add(other)

    def __sub__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """Python - operator."""
        return self.subtract(other)

    def __mul__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """Python * operator."""
        return self.multiply(other)

    def __truediv__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """Python / operator."""
        return self.divide(other)

    def __mod__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """Python % operator."""
        return self.modulo(other)

    def __pow__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """Python ** operator."""
        return self.power(other)

    def __floordiv__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """Python // operator."""
        return self.floor_divide(other)

    # ========================================
    # Reverse Python Arithmetic Operators
    # ========================================
    # These are called when the left operand doesn't support the operation
    # e.g., 5 + col("x") calls col("x").__radd__(5)

    def __radd__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Reverse addition (other + self).

        Called when: literal + ExpressionBuilder
        Example: 5 + col("x") → col("x").__radd__(5)
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticIterableExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.ADD,
            other_node,
            self._node
        )
        return self.create(node)

    def __rsub__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Reverse subtraction (other - self).

        Called when: literal - ExpressionBuilder
        Example: 10 - col("x") → col("x").__rsub__(10)
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.SUBTRACT,
            other_node,
            self._node
        )
        return self.create(node)

    def __rmul__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Reverse multiplication (other * self).

        Called when: literal * ExpressionBuilder
        Example: 3 * col("x") → col("x").__rmul__(3)
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticIterableExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.MULTIPLY,
            other_node,
            self._node
        )
        return self.create(node)

    def __rtruediv__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Reverse division (other / self).

        Called when: literal / ExpressionBuilder
        Example: 100 / col("x") → col("x").__rtruediv__(100)
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.DIVIDE,
            other_node,
            self._node
        )
        return self.create(node)

    def __rmod__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Reverse modulo (other % self).

        Called when: literal % ExpressionBuilder
        Example: 10 % col("x") → col("x").__rmod__(10)
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.MODULO,
            other_node,
            self._node
        )
        return self.create(node)

    def __rpow__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Reverse power (other ** self).

        Called when: literal ** ExpressionBuilder
        Example: 2 ** col("x") → col("x").__rpow__(2)
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.POWER,
            other_node,
            self._node
        )
        return self.create(node)

    def __rfloordiv__(self, other: Union[ExpressionBuilder, ExpressionNode, Any]) -> ExpressionBuilder:
        """
        Reverse floor division (other // self).

        Called when: literal // ExpressionBuilder
        Example: 10 // col("x") → col("x").__rfloordiv__(10)
        """

        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.FLOOR_DIVIDE,
            other_node,
            self._node
        )
        return self.create(node)
