"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace






class ScalarArithmeticExpressionProtocol(Protocol):
    """Protocol for arithmetic operations.

    Auto-generated from Substrait arithmetic extension.
    """

    def add(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Add two values.

        Substrait: add
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def subtract(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Subtract one value from another.

        Substrait: subtract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def multiply(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Multiply two values.

        Substrait: multiply
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def divide(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None, on_domain_error: Any = None, on_division_by_zero: Any = None) -> SupportedExpressions:
        """Divide x by y. In the case of integer division, partial values are truncated (i.e. rounded towards 0). The `on_division_by_zero` option governs behavior in cases where y is 0.  If the option is IEEE then the IEEE754 standard is followed: all values except +/-infinity return NaN and +/-infinity are unchanged. If the option is LIMIT then the result is +/-infinity in all cases. If either x or y are NaN then behavior will be governed by `on_domain_error`. If x and y are both +/-infinity, behavior will be governed by `on_domain_error`.


        Substrait: divide
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def negate(self, x: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Negation of the value

        Substrait: negate
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def modulus(self, x: SupportedExpressions, y: SupportedExpressions, /, division_type: Any = None, overflow: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
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

    def power(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Take the power with x as the base and y as exponent.

        Substrait: power
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...




#     def sqrt(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
#         """Square root of the value

#         Substrait: sqrt
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def exp(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """The mathematical constant e, raised to the power of the value.

#         Substrait: exp
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def cos(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Get the cosine of a value in radians.

#         Substrait: cos
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sin(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Get the sine of a value in radians.

#         Substrait: sin
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def tan(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Get the tangent of a value in radians.

#         Substrait: tan
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def cosh(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Get the hyperbolic cosine of a value in radians.

#         Substrait: cosh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sinh(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Get the hyperbolic sine of a value in radians.

#         Substrait: sinh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def tanh(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Get the hyperbolic tangent of a value in radians.

#         Substrait: tanh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def acos(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
#         """Get the arccosine of a value in radians.

#         Substrait: acos
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def asin(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
#         """Get the arcsine of a value in radians.

#         Substrait: asin
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def atan(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Get the arctangent of a value in radians.

#         Substrait: atan
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def acosh(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
#         """Get the hyperbolic arccosine of a value in radians.

#         Substrait: acosh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def asinh(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Get the hyperbolic arcsine of a value in radians.

#         Substrait: asinh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def atanh(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
#         """Get the hyperbolic arctangent of a value in radians.

#         Substrait: atanh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def atan2(self, x: SupportedExpressions, y: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
#         """Get the arctangent of values given as x/y pairs.

#         Substrait: atan2
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def radians(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Converts angle `x` in degrees to radians.


#         Substrait: radians
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def degrees(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Converts angle `x` in radians to degrees.


#         Substrait: degrees
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def abs(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
#         """Calculate the absolute value of the argument.
# Integer values allow the specification of overflow behavior to handle the unevenness of the twos complement, e.g. Int8 range [-128 : 127].


#         Substrait: abs
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sign(self, x: SupportedExpressions) -> SupportedExpressions:
#         """Return the signedness of the argument.
# Integer values return signedness with the same type as the input. Possible return values are [-1, 0, 1]
# Floating point values return signedness with the same type as the input. Possible return values are [-1.0, -0.0, 0.0, 1.0, NaN]


#         Substrait: sign
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def factorial(self, n: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
#         """Return the factorial of a given integer input.
# The factorial of 0! is 1 by convention.
# Negative inputs will raise an error.


#         Substrait: factorial
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def bitwise_not(self, x: SupportedExpressions) -> SupportedExpressions:
#         """Return the bitwise NOT result for one integer input.


#         Substrait: bitwise_not
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def bitwise_and(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Return the bitwise AND result for two integer inputs.


#         Substrait: bitwise_and
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def bitwise_or(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Return the bitwise OR result for two given integer inputs.


#         Substrait: bitwise_or
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def bitwise_xor(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Return the bitwise XOR result for two integer inputs.


#         Substrait: bitwise_xor
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def shift_left(self, base: SupportedExpressions, shift: SupportedExpressions) -> SupportedExpressions:
#         """Bitwise shift left. The vacant (least-significant) bits are filled with zeros. Params:
#   base – the base number to shift.
#   shift – number of bits to left shift.

#         Substrait: shift_left
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def shift_right(self, base: SupportedExpressions, shift: SupportedExpressions) -> SupportedExpressions:
#         """Bitwise (signed) shift right. The vacant (most-significant) bits are filled with zeros if the base number is positive or with ones if the base number is negative, thus preserving the sign of the resulting number. Params:
#   base – the base number to shift.
#   shift – number of bits to right shift.

#         Substrait: shift_right
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def shift_right_unsigned(self, base: SupportedExpressions, shift: SupportedExpressions) -> SupportedExpressions:
#         """Bitwise unsigned shift right. The vacant (most-significant) bits are filled with zeros. Params:
#   base – the base number to shift.
#   shift – number of bits to right shift.

#         Substrait: shift_right_unsigned
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sum(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
#         """Sum a set of values. The sum of zero elements yields null.

#         Substrait: sum
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sum0(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
#         """Sum a set of values. The sum of zero elements yields zero.
# Null values are ignored.


#         Substrait: sum0
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def avg(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
#         """Average a set of values. For integral types, this truncates partial values.

#         Substrait: avg
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def min(self, x: SupportedExpressions) -> SupportedExpressions:
#         """Min a set of values.

#         Substrait: min
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def max(self, x: SupportedExpressions) -> SupportedExpressions:
#         """Max a set of values.

#         Substrait: max
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def product(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
#         """Product of a set of values. Returns 1 for empty input.

#         Substrait: product
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def std_dev(self, x: SupportedExpressions, rounding: Any = None, distribution: Any = None) -> SupportedExpressions:
#         """Calculates standard-deviation for a set of values.

#         Substrait: std_dev
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def variance(self, x: SupportedExpressions, rounding: Any = None, distribution: Any = None) -> SupportedExpressions:
#         """Calculates variance for a set of values.

#         Substrait: variance
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def corr(self, x: SupportedExpressions, y: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Calculates the value of Pearson's correlation coefficient between `x` and `y`. If there is no input, null is returned.


#         Substrait: corr
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def mode(self, x: SupportedExpressions) -> SupportedExpressions:
#         """Calculates mode for a set of values. If there is no input, null is returned.


#         Substrait: mode
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def median(self, precision: SupportedExpressions, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Calculate the median for a set of values.
# Returns null if applied to zero records. For the integer implementations, the rounding option determines how the median should be rounded if it ends up midway between two values. For the floating point implementations, they specify the usual floating point rounding mode.


#         Substrait: median
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def quantile(self, boundaries: SupportedExpressions, precision: SupportedExpressions, n: SupportedExpressions, distribution: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
#         """Calculates quantiles for a set of values.
# This function will divide the aggregated values (passed via the distribution argument) over N equally-sized bins, where N is passed via a constant argument. It will then return the values at the boundaries of these bins in list form. If the input is appropriately sorted, this computes the quantiles of the distribution.
# The function can optionally return the first and/or last element of the input, as specified by the `boundaries` argument. If the input is appropriately sorted, this will thus be the minimum and/or maximum values of the distribution.
# When the boundaries do not lie exactly on elements of the incoming distribution, the function will interpolate between the two nearby elements. If the interpolated value cannot be represented exactly, the `rounding` option controls how the value should be selected or computed.
# The function fails and returns null in the following cases:
#   - `n` is null or less than one;
#   - any value in `distribution` is null.

# The function returns an empty list if `n` equals 1 and `boundaries` is set to `NEITHER`.


#         Substrait: quantile
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...


class ScalarArithmeticBuilderProtocol(Protocol):
    """Builder protocol for arithmetic operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    def add(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Add two values.

        Substrait: add
        """
        ...

    def subtract(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Subtract one value from another.

        Substrait: subtract
        """
        ...

    def multiply(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Multiply two values.

        Substrait: multiply
        """
        ...

    def divide(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Divide x by y.

        Substrait: divide
        """
        ...

    def negate(self) -> "BaseNamespace":
        """Negate the value.

        Substrait: negate
        """
        ...

    def modulus(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Calculate the remainder when dividing by other.

        Substrait: modulus
        """
        ...

    def power(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Raise to the power of other.

        Substrait: power
        """
        ...
