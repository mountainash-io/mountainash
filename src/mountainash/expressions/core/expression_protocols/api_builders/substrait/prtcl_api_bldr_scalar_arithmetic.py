"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode


class SubstraitScalarArithmeticAPIBuilderProtocol(Protocol):
    """Builder protocol for arithmetic operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def add(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Add two values.

        Substrait: add
        """
        ...

    def subtract(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Subtract one value from another.

        Substrait: subtract
        """
        ...

    def rsubtract(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Subtract one value from another.

        Substrait: subtract
        """
        ...

    def multiply(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Multiply two values.

        Substrait: multiply
        """
        ...

    def divide(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Divide x by y.

        Substrait: divide
        """
        ...

    def rdivide(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Divide x by y.

        Substrait: divide
        """
        ...



    def modulus(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Calculate the remainder when dividing by other.

        Substrait: modulus
        """
        ...

    def rmodulus(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Calculate the remainder when dividing by other.

        Substrait: modulus
        """
        ...

    def power(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Raise to the power of other.

        Substrait: power
        """
        ...


    def rpower(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
        """Raise to the power of other.

        Substrait: power
        """
        ...

    def negate(self) -> BaseExpressionAPI:
        """Negate the value (-self).

        Substrait: negate
        """
        ...



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

    def sin(self) -> BaseExpressionAPI:
        """Get the sine of a value in radians."""
        ...

    def cos(self) -> BaseExpressionAPI:
        """Get the cosine of a value in radians."""
        ...

    def tan(self) -> BaseExpressionAPI:
        """Get the tangent of a value in radians."""
        ...

    def sinh(self) -> BaseExpressionAPI:
        """Get the hyperbolic sine of a value."""
        ...

    def cosh(self) -> BaseExpressionAPI:
        """Get the hyperbolic cosine of a value."""
        ...

    def tanh(self) -> BaseExpressionAPI:
        """Get the hyperbolic tangent of a value."""
        ...

    def asin(self) -> BaseExpressionAPI:
        """Get the arcsine of a value in radians."""
        ...

    def acos(self) -> BaseExpressionAPI:
        """Get the arccosine of a value in radians."""
        ...

    def atan(self) -> BaseExpressionAPI:
        """Get the arctangent of a value in radians."""
        ...

    def asinh(self) -> BaseExpressionAPI:
        """Get the hyperbolic arcsine of a value."""
        ...

    def acosh(self) -> BaseExpressionAPI:
        """Get the hyperbolic arccosine of a value."""
        ...

    def atanh(self) -> BaseExpressionAPI:
        """Get the hyperbolic arctangent of a value."""
        ...

    def atan2(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Get the arctangent of y/x (self/other) in radians."""
        ...

    def radians(self) -> BaseExpressionAPI:
        """Convert angle from degrees to radians."""
        ...

    def degrees(self) -> BaseExpressionAPI:
        """Convert angle from radians to degrees."""
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
