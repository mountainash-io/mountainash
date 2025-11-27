"""Arithmetic operations namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseNamespace
from ..protocols import ENUM_ARITHMETIC_OPERATORS, ArithmeticBuilderProtocol
from ..expression_nodes import (
    ArithmeticExpressionNode,
    ArithmeticIterableExpressionNode,
)

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class ArithmeticNamespace(BaseNamespace, ArithmeticBuilderProtocol):
    """
    Arithmetic operations namespace.

    Provides arithmetic operators as named methods.
    Python operators (__add__, __sub__, etc.) are on the main API class.

    Methods:
        add: Addition (+)
        subtract: Subtraction (-)
        multiply: Multiplication (*)
        divide: Division (/)
        modulo: Modulo (%)
        power: Exponentiation (**)
        floor_divide: Floor division (//)
    """

    # ========================================
    # Binary Arithmetic Operations
    # ========================================

    def subtract(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Subtraction: self - other.

        Args:
            other: Value or expression to subtract.

        Returns:
            New ExpressionAPI with subtraction node.
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.SUBTRACT,
            self._node,
            other_node,
        )
        return self._build(node)

    def rsubtract(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Reverse subtraction: other - self.

        Used by __rsub__ when self is on the right side of -.

        Args:
            other: Value or expression to subtract from.

        Returns:
            New ExpressionAPI with subtraction node (other - self).
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.SUBTRACT,
            other_node,
            self._node,
        )
        return self._build(node)

    def divide(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Division: self / other.

        Args:
            other: Value or expression to divide by.

        Returns:
            New ExpressionAPI with division node.
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.DIVIDE,
            self._node,
            other_node,
        )
        return self._build(node)

    def rdivide(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Reverse division: other / self.

        Used by __rtruediv__ when self is on the right side of /.

        Args:
            other: Value or expression to be divided.

        Returns:
            New ExpressionAPI with division node (other / self).
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.DIVIDE,
            other_node,
            self._node,
        )
        return self._build(node)

    def modulo(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Modulo: self % other.

        Args:
            other: Value or expression for modulo operation.

        Returns:
            New ExpressionAPI with modulo node.
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.MODULO,
            self._node,
            other_node,
        )
        return self._build(node)

    def rmodulo(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Reverse modulo: other % self.

        Used by __rmod__ when self is on the right side of %.

        Args:
            other: Value or expression to take modulo of.

        Returns:
            New ExpressionAPI with modulo node (other % self).
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.MODULO,
            other_node,
            self._node,
        )
        return self._build(node)

    def power(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Exponentiation: self ** other.

        Args:
            other: Exponent value or expression.

        Returns:
            New ExpressionAPI with power node.
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.POWER,
            self._node,
            other_node,
        )
        return self._build(node)

    def rpower(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Reverse exponentiation: other ** self.

        Used by __rpow__ when self is on the right side of **.

        Args:
            other: Base value or expression.

        Returns:
            New ExpressionAPI with power node (other ** self).
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.POWER,
            other_node,
            self._node,
        )
        return self._build(node)

    def floor_divide(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Floor division: self // other.

        Args:
            other: Value or expression to divide by.

        Returns:
            New ExpressionAPI with floor division node.
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.FLOOR_DIVIDE,
            self._node,
            other_node,
        )
        return self._build(node)

    def rfloor_divide(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Reverse floor division: other // self.

        Used by __rfloordiv__ when self is on the right side of //.

        Args:
            other: Value or expression to be divided.

        Returns:
            New ExpressionAPI with floor division node (other // self).
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.FLOOR_DIVIDE,
            other_node,
            self._node,
        )
        return self._build(node)

    # ========================================
    # N-ary Arithmetic Operations (Iterable)
    # ========================================

    def add(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Addition (+).

        Can be chained with multiple operands.

        Args:
            other: Value or expression to add.

        Returns:
            New ExpressionAPI with addition node.
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticIterableExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.ADD,
            self._node,
            other_node,
        )
        return self._build(node)

    def multiply(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Multiplication (*).

        Can be chained with multiple operands.

        Args:
            other: Value or expression to multiply by.

        Returns:
            New ExpressionAPI with multiplication node.
        """
        other_node = self._to_node_or_value(other)
        node = ArithmeticIterableExpressionNode(
            ENUM_ARITHMETIC_OPERATORS.MULTIPLY,
            self._node,
            other_node,
        )
        return self._build(node)
