"""Arithmetic operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarArithmeticBuilderProtocol for arithmetic operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import KEY_SCALAR_ARITHMETIC
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.substrait import SubstraitScalarArithmeticAPIBuilderProtocol


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitArithmeticAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarArithmeticAPIBuilderProtocol):
    """
    Arithmetic operations APIBuilder (Substrait-aligned).

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

    def add(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Addition: self + other.

        Args:
            other: Value or expression to add.

        Returns:
            New ExpressionAPI with addition node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.ADD,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def subtract(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Subtraction: self - other.

        Args:
            other: Value or expression to subtract.

        Returns:
            New ExpressionAPI with subtraction node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.SUBTRACT,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def rsubtract(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Reverse subtraction: other - self.

        Used by __rsub__ when self is on the right side of -.

        Args:
            other: Value or expression to subtract from.

        Returns:
            New ExpressionAPI with subtraction node (other - self).
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.SUBTRACT,
            arguments=[other_node, self._node],
        )
        return self._build(node)

    def multiply(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Multiplication: self * other.

        Args:
            other: Value or expression to multiply by.

        Returns:
            New ExpressionAPI with multiplication node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.MULTIPLY,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def divide(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Division: self / other.

        Args:
            other: Value or expression to divide by.

        Returns:
            New ExpressionAPI with division node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.DIVIDE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def rdivide(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Reverse division: other / self.

        Used by __rtruediv__ when self is on the right side of /.

        Args:
            other: Value or expression to be divided.

        Returns:
            New ExpressionAPI with division node (other / self).
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.DIVIDE,
            arguments=[other_node, self._node],
        )
        return self._build(node)

    def modulo(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Modulo: self % other.

        Args:
            other: Value or expression for modulo operation.

        Returns:
            New ExpressionAPI with modulo node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.MODULO,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def rmodulo(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Reverse modulo: other % self.

        Used by __rmod__ when self is on the right side of %.

        Args:
            other: Value or expression to take modulo of.

        Returns:
            New ExpressionAPI with modulo node (other % self).
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.MODULO,
            arguments=[other_node, self._node],
        )
        return self._build(node)

    def power(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Exponentiation: self ** other.

        Args:
            other: Exponent value or expression.

        Returns:
            New ExpressionAPI with power node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.POWER,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def rpower(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Reverse exponentiation: other ** self.

        Used by __rpow__ when self is on the right side of **.

        Args:
            other: Base value or expression.

        Returns:
            New ExpressionAPI with power node (other ** self).
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.POWER,
            arguments=[other_node, self._node],
        )
        return self._build(node)

    def floor_divide(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Floor division: self // other.

        Args:
            other: Value or expression to divide by.

        Returns:
            New ExpressionAPI with floor division node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_ARITHMETIC.FLOOR_DIVIDE,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def rfloor_divide(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Reverse floor division: other // self.

        Used by __rfloordiv__ when self is on the right side of //.

        Args:
            other: Value or expression to be divided.

        Returns:
            New ExpressionAPI with floor division node (other // self).
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=MOUNTAINASH_ARITHMETIC.FLOOR_DIVIDE,
            arguments=[other_node, self._node],
        )
        return self._build(node)

    # ========================================
    # Unary Arithmetic Operations
    # ========================================

    def negate(self) -> BaseExpressionAPI:
        """
        Negation: -self.

        Substrait: negate

        Returns:
            New ExpressionAPI with negation node.
        """
        node = ScalarFunctionNode(
            function_key=KEY_SCALAR_ARITHMETIC.NEGATE,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Aliases for Protocol Compatibility
    # ========================================

    def modulus(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Alias for modulo() for Substrait protocol compatibility.

        Substrait: modulus

        Args:
            other: Value or expression for modulo operation.

        Returns:
            New ExpressionAPI with modulo node.
        """
        return self.modulo(other)


# Alias for consistency with other scalar APIBuilders
ScalarArithmeticAPIBuilder = ArithmeticAPIBuilder
