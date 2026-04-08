"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Protocol, Optional

from mountainash.core.types import ExpressionT


class SubstraitScalarArithmeticExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for scalar arithmetic operations.

    Auto-generated from Substrait arithmetic extension.
    Function type: scalar
    """

    def add(self, x: ExpressionT, y: ExpressionT, /, overflow: Optional[str] = None) -> ExpressionT:
        """Add two values.

        Substrait: add
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def subtract(self, x: ExpressionT, y: ExpressionT, /, overflow: Optional[str] = None) -> ExpressionT:
        """Subtract one value from another.

        Substrait: subtract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def multiply(self, x: ExpressionT, y: ExpressionT, /, overflow: Optional[str] = None) -> ExpressionT:
        """Multiply two values.

        Substrait: multiply
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def divide(self, x: ExpressionT, y: ExpressionT, /, overflow: Optional[str] = None, on_domain_error: Optional[str] = None, on_division_by_zero: Optional[str] = None) -> ExpressionT:
        """Divide x by y. In the case of integer division, partial values are truncated (i.e. rounded towards 0). The `on_division_by_zero` option governs behavior in cases where y is 0.  If the option is IEEE then the IEEE754 standard is followed: all values except +/-infinity return NaN and +/-infinity are unchanged. If the option is LIMIT then the result is +/-infinity in all cases. If either x or y are NaN then behavior will be governed by `on_domain_error`. If x and y are both +/-infinity, behavior will be governed by `on_domain_error`.


        Substrait: divide
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def negate(self, x: ExpressionT, /, overflow: Optional[str] = None) -> ExpressionT:
        """Negation of the value

        Substrait: negate
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def modulus(self, x: ExpressionT, y: ExpressionT, /, division_type: Optional[str] = None, overflow: Optional[str] = None, on_domain_error: Optional[str] = None) -> ExpressionT:
        """Calculate the remainder (r) when dividing dividend (x) by divisor (y).
In mathematics, many conventions for the modulus (mod) operation exists. The result of a mod operation depends on the software implementation and underlying hardware. Substrait is a format for describing compute operations on structured data and designed for interoperability. Therefore the user is responsible for determining a definition of division as defined by the quotient (q).
The following basic conditions of division are satisfied: (1) q ∈ ℤ (the quotient is an integer) (2) x = y * q + r (division rule) (3) abs(r) < abs(y) where q is the quotient.
The `division_type` option determines the mathematical definition of quotient to use in the above definition of division.
When `division_type`=TRUNCATE, q = trunc(x/y). When `division_type`=FLOOR, q = floor(x/y).
In the cases of TRUNCATE and FLOOR division: remainder r = x - round_func(x/y)
The `on_domain_error` option governs behavior in cases where y is 0, y is +/-inf, or x is +/-inf. In these cases the mod is undefined. The `overflow` option governs behavior when integer overflow occurs. If x and y are both 0 or both +/-infinity, behavior will be governed by `on_domain_error`.


        Substrait: modulus
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def power(self, x: ExpressionT, y: ExpressionT, /, overflow: Optional[str] = None) -> ExpressionT:
        """Take the power with x as the base and y as exponent.

        Substrait: power
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sqrt(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None) -> ExpressionT:
        """Square root of the value

        Substrait: sqrt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def exp(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """The mathematical constant e, raised to the power of the value.

        Substrait: exp
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def abs(self, x: ExpressionT, /, overflow: Optional[str] = None) -> ExpressionT:
        """Calculate the absolute value of the argument.
Integer values allow the specification of overflow behavior to handle the unevenness of the twos complement, e.g. Int8 range [-128 : 127].


        Substrait: abs
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sign(self, x: ExpressionT, /) -> ExpressionT:
        """Return the signedness of the argument.
Integer values return signedness with the same type as the input. Possible return values are [-1, 0, 1]
Floating point values return signedness with the same type as the input. Possible return values are [-1.0, -0.0, 0.0, 1.0, NaN]


        Substrait: sign
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def factorial(self, n: ExpressionT, /, overflow: Optional[str] = None) -> ExpressionT:
        """Return the factorial of a given integer input.
The factorial of 0! is 1 by convention.
Negative inputs will raise an error.


        Substrait: factorial
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sin(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Get the sine of a value in radians.

        Substrait: sin
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def cos(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Get the cosine of a value in radians.

        Substrait: cos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...


    def tan(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Get the tangent of a value in radians.

        Substrait: tan
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...


    def sinh(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Get the hyperbolic sine of a value in radians.

        Substrait: sinh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...


    def cosh(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Get the hyperbolic cosine of a value in radians.

        Substrait: cosh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...


    def tanh(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Get the hyperbolic tangent of a value in radians.

        Substrait: tanh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def asin(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None) -> ExpressionT:
        """Get the arcsine of a value in radians.

        Substrait: asin
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def acos(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None) -> ExpressionT:
        """Get the arccosine of a value in radians.

        Substrait: acos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atan(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Get the arctangent of a value in radians.

        Substrait: atan
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def asinh(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Get the hyperbolic arcsine of a value in radians.

        Substrait: asinh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def acosh(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None) -> ExpressionT:
        """Get the hyperbolic arccosine of a value in radians.

        Substrait: acosh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atanh(self, x: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None) -> ExpressionT:
        """Get the hyperbolic arctangent of a value in radians.

        Substrait: atanh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atan2(self, x: ExpressionT, y: ExpressionT, /, rounding: Optional[str] = None, on_domain_error: Optional[str] = None) -> ExpressionT:
        """Get the arctangent of values given as x/y pairs.

        Substrait: atan2
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def radians(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Converts angle `x` in degrees to radians.


        Substrait: radians
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def degrees(self, x: ExpressionT, /, rounding: Optional[str] = None) -> ExpressionT:
        """Converts angle `x` in radians to degrees.


        Substrait: degrees
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...


    def bitwise_not(self, x: ExpressionT, /) -> ExpressionT:
        """Return the bitwise NOT result for one integer input.


        Substrait: bitwise_not
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_and(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """Return the bitwise AND result for two integer inputs.


        Substrait: bitwise_and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_or(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """Return the bitwise OR result for two given integer inputs.


        Substrait: bitwise_or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_xor(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """Return the bitwise XOR result for two integer inputs.


        Substrait: bitwise_xor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_left(self, base: ExpressionT, shift: ExpressionT, /) -> ExpressionT:
        """Bitwise shift left. The vacant (least-significant) bits are filled with zeros. Params:
  base – the base number to shift.
  shift – number of bits to left shift.

        Substrait: shift_left
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_right(self, base: ExpressionT, shift: ExpressionT, /) -> ExpressionT:
        """Bitwise (signed) shift right. The vacant (most-significant) bits are filled with zeros if the base number is positive or with ones if the base number is negative, thus preserving the sign of the resulting number. Params:
  base – the base number to shift.
  shift – number of bits to right shift.

        Substrait: shift_right
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_right_unsigned(self, base: ExpressionT, shift: ExpressionT, /) -> ExpressionT:
        """Bitwise unsigned shift right. The vacant (most-significant) bits are filled with zeros. Params:
  base – the base number to shift.
  shift – number of bits to right shift.

        Substrait: shift_right_unsigned
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...
