"""Arithmetic operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarArithmeticBuilderProtocol for arithmetic operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.substrait import SubstraitScalarArithmeticAPIBuilderProtocol


if TYPE_CHECKING:
    from mountainash_expressions.core.expression_nodes import ExpressionNode, ScalarFunctionNode
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitScalarArithmeticAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarArithmeticAPIBuilderProtocol):
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE,
            arguments=[other_node, self._node],
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
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
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER,
            arguments=[other_node, self._node],
        )
        return self._build(node)

    # # ========================================
    # # Unary Arithmetic Operations
    # # ========================================

    # def negate(self) -> BaseExpressionAPI:
    #     """
    #     Negation: -self.

    #     Substrait: negate

    #     Returns:
    #         New ExpressionAPI with negation node.
    #     """
    #     node = ScalarFunctionNode(
    #         function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE,
    #         arguments=[self._node],
    #     )
    #     return self._build(node)




    def sqrt(self, rounding: Any = None, on_domain_error: Any = None) -> BaseExpressionAPI:
        """Square root of the value

        Substrait: sqrt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def exp(self, rounding: Any = None) -> BaseExpressionAPI:
        """The mathematical constant e, raised to the power of the value.

        Substrait: exp
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def abs(self, overflow: Any = None) -> BaseExpressionAPI:
        """Calculate the absolute value of the argument.
Integer values allow the specification of overflow behavior to handle the unevenness of the twos complement, e.g. Int8 range [-128 : 127].


        Substrait: abs
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sign(self) -> BaseExpressionAPI:
        """Return the signedness of the argument.
Integer values return signedness with the same type as the input. Possible return values are [-1, 0, 1]
Floating point values return signedness with the same type as the input. Possible return values are [-1.0, -0.0, 0.0, 1.0, NaN]


        Substrait: sign
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def factorial(self, overflow: Any = None) -> BaseExpressionAPI:
        """Return the factorial of a given integer input.
The factorial of 0! is 1 by convention.
Negative inputs will raise an error.


        Substrait: factorial
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sin(self, rounding: Any = None) -> BaseExpressionAPI:
        """Get the sine of a value in radians.

        Substrait: sin
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def cos(self, rounding: Any = None) -> BaseExpressionAPI:
        """Get the cosine of a value in radians.

        Substrait: cos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...



    def tan(self,  rounding: Any = None) -> BaseExpressionAPI:
        """Get the tangent of a value in radians.

        Substrait: tan
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...


    def sinh(self, rounding: Any = None) -> BaseExpressionAPI:
        """Get the hyperbolic sine of a value in radians.

        Substrait: sinh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...


    def cosh(self, rounding: Any = None) -> BaseExpressionAPI:
        """Get the hyperbolic cosine of a value in radians.

        Substrait: cosh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...


    def tanh(self, rounding: Any = None) -> BaseExpressionAPI:
        """Get the hyperbolic tangent of a value in radians.

        Substrait: tanh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def asin(self, rounding: Any = None, on_domain_error: Any = None) -> BaseExpressionAPI:
        """Get the arcsine of a value in radians.

        Substrait: asin
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def acos(self, rounding: Any = None, on_domain_error: Any = None) -> BaseExpressionAPI:
        """Get the arccosine of a value in radians.

        Substrait: acos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atan(self,rounding: Any = None) -> BaseExpressionAPI:
        """Get the arctangent of a value in radians.

        Substrait: atan
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def asinh(self,  rounding: Any = None) -> BaseExpressionAPI:
        """Get the hyperbolic arcsine of a value in radians.

        Substrait: asinh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def acosh(self, rounding: Any = None, on_domain_error: Any = None) -> BaseExpressionAPI:
        """Get the hyperbolic arccosine of a value in radians.

        Substrait: acosh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atanh(self, rounding: Any = None, on_domain_error: Any = None) -> BaseExpressionAPI:
        """Get the hyperbolic arctangent of a value in radians.

        Substrait: atanh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atan2(self, other: Union[BaseExpressionAPI, ExpressionNode, Any],  rounding: Any = None, on_domain_error: Any = None) -> BaseExpressionAPI:
        """Get the arctangent of values given as x/y pairs.

        Substrait: atan2
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def radians(self,  rounding: Any = None) -> BaseExpressionAPI:
        """Converts angle `x` in degrees to radians.


        Substrait: radians
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def degrees(self, rounding: Any = None) -> BaseExpressionAPI:
        """Converts angle `x` in radians to degrees.


        Substrait: degrees
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...






    def bitwise_not(self) -> BaseExpressionAPI:
        """Return the bitwise NOT result for one integer input.


        Substrait: bitwise_not
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_and(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Return the bitwise AND result for two integer inputs.


        Substrait: bitwise_and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_or(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Return the bitwise OR result for two given integer inputs.


        Substrait: bitwise_or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_xor(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Return the bitwise XOR result for two integer inputs.


        Substrait: bitwise_xor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_left(self, shift: Union[BaseExpressionAPI, ExpressionNode, int], /) -> BaseExpressionAPI:
        """Bitwise shift left. The vacant (least-significant) bits are filled with zeros. Params:
  base – the base number to shift.
  shift – number of bits to left shift.

        Substrait: shift_left
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_right(self, shift: Union[BaseExpressionAPI, ExpressionNode, int], /) -> BaseExpressionAPI:
        """Bitwise (signed) shift right. The vacant (most-significant) bits are filled with zeros if the base number is positive or with ones if the base number is negative, thus preserving the sign of the resulting number. Params:
  base – the base number to shift.
  shift – number of bits to right shift.

        Substrait: shift_right
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_right_unsigned(self, shift: Union[BaseExpressionAPI, ExpressionNode, int], /) -> BaseExpressionAPI:
        """Bitwise unsigned shift right. The vacant (most-significant) bits are filled with zeros. Params:
  base – the base number to shift.
  shift – number of bits to right shift.

        Substrait: shift_right_unsigned
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...
