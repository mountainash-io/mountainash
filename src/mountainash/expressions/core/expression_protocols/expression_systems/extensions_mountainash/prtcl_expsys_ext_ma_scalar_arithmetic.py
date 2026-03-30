"""Mountainash arithmetic extension protocol.

Mountainash Extension: Arithmetic
URI: file://extensions/functions_arithmetic.yaml

Extensions beyond Substrait standard:
- floor_divide: Floor division (Python's //)
"""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarArithmeticExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for Mountainash arithmetic extensions.

    These operations extend beyond the Substrait standard arithmetic
    functions to provide additional arithmetic operations commonly
    needed in data processing.
    """

    def floor_divide(
        self,
        x: ExpressionT,
        y: ExpressionT,
        /,
    ) -> ExpressionT:
        """Floor division: x // y.

        Divides x by y and returns the floor of the result.
        This is equivalent to Python's // operator.

        Args:
            x: Dividend.
            y: Divisor.

        Returns:
            Floor of x / y.
        """
        ...





#     def sqrt(self, x: ExpressionT, rounding: Any = None, on_domain_error: Any = None) -> ExpressionT:
#         """Square root of the value

#         Substrait: sqrt
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def exp(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """The mathematical constant e, raised to the power of the value.

#         Substrait: exp
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def cos(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Get the cosine of a value in radians.

#         Substrait: cos
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sin(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Get the sine of a value in radians.

#         Substrait: sin
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def tan(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Get the tangent of a value in radians.

#         Substrait: tan
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def cosh(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Get the hyperbolic cosine of a value in radians.

#         Substrait: cosh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sinh(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Get the hyperbolic sine of a value in radians.

#         Substrait: sinh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def tanh(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Get the hyperbolic tangent of a value in radians.

#         Substrait: tanh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def acos(self, x: ExpressionT, rounding: Any = None, on_domain_error: Any = None) -> ExpressionT:
#         """Get the arccosine of a value in radians.

#         Substrait: acos
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def asin(self, x: ExpressionT, rounding: Any = None, on_domain_error: Any = None) -> ExpressionT:
#         """Get the arcsine of a value in radians.

#         Substrait: asin
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def atan(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Get the arctangent of a value in radians.

#         Substrait: atan
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def acosh(self, x: ExpressionT, rounding: Any = None, on_domain_error: Any = None) -> ExpressionT:
#         """Get the hyperbolic arccosine of a value in radians.

#         Substrait: acosh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def asinh(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Get the hyperbolic arcsine of a value in radians.

#         Substrait: asinh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def atanh(self, x: ExpressionT, rounding: Any = None, on_domain_error: Any = None) -> ExpressionT:
#         """Get the hyperbolic arctangent of a value in radians.

#         Substrait: atanh
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def atan2(self, x: ExpressionT, y: ExpressionT, rounding: Any = None, on_domain_error: Any = None) -> ExpressionT:
#         """Get the arctangent of values given as x/y pairs.

#         Substrait: atan2
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def radians(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Converts angle `x` in degrees to radians.


#         Substrait: radians
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def degrees(self, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Converts angle `x` in radians to degrees.


#         Substrait: degrees
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def abs(self, x: ExpressionT, overflow: Any = None) -> ExpressionT:
#         """Calculate the absolute value of the argument.
# Integer values allow the specification of overflow behavior to handle the unevenness of the twos complement, e.g. Int8 range [-128 : 127].


#         Substrait: abs
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sign(self, x: ExpressionT) -> ExpressionT:
#         """Return the signedness of the argument.
# Integer values return signedness with the same type as the input. Possible return values are [-1, 0, 1]
# Floating point values return signedness with the same type as the input. Possible return values are [-1.0, -0.0, 0.0, 1.0, NaN]


#         Substrait: sign
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def factorial(self, n: ExpressionT, overflow: Any = None) -> ExpressionT:
#         """Return the factorial of a given integer input.
# The factorial of 0! is 1 by convention.
# Negative inputs will raise an error.


#         Substrait: factorial
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def bitwise_not(self, x: ExpressionT) -> ExpressionT:
#         """Return the bitwise NOT result for one integer input.


#         Substrait: bitwise_not
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def bitwise_and(self, x: ExpressionT, y: ExpressionT) -> ExpressionT:
#         """Return the bitwise AND result for two integer inputs.


#         Substrait: bitwise_and
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def bitwise_or(self, x: ExpressionT, y: ExpressionT) -> ExpressionT:
#         """Return the bitwise OR result for two given integer inputs.


#         Substrait: bitwise_or
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def bitwise_xor(self, x: ExpressionT, y: ExpressionT) -> ExpressionT:
#         """Return the bitwise XOR result for two integer inputs.


#         Substrait: bitwise_xor
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def shift_left(self, base: ExpressionT, shift: ExpressionT) -> ExpressionT:
#         """Bitwise shift left. The vacant (least-significant) bits are filled with zeros. Params:
#   base – the base number to shift.
#   shift – number of bits to left shift.

#         Substrait: shift_left
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def shift_right(self, base: ExpressionT, shift: ExpressionT) -> ExpressionT:
#         """Bitwise (signed) shift right. The vacant (most-significant) bits are filled with zeros if the base number is positive or with ones if the base number is negative, thus preserving the sign of the resulting number. Params:
#   base – the base number to shift.
#   shift – number of bits to right shift.

#         Substrait: shift_right
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def shift_right_unsigned(self, base: ExpressionT, shift: ExpressionT) -> ExpressionT:
#         """Bitwise unsigned shift right. The vacant (most-significant) bits are filled with zeros. Params:
#   base – the base number to shift.
#   shift – number of bits to right shift.

#         Substrait: shift_right_unsigned
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sum(self, x: ExpressionT, overflow: Any = None) -> ExpressionT:
#         """Sum a set of values. The sum of zero elements yields null.

#         Substrait: sum
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def sum0(self, x: ExpressionT, overflow: Any = None) -> ExpressionT:
#         """Sum a set of values. The sum of zero elements yields zero.
# Null values are ignored.


#         Substrait: sum0
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def avg(self, x: ExpressionT, overflow: Any = None) -> ExpressionT:
#         """Average a set of values. For integral types, this truncates partial values.

#         Substrait: avg
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def min(self, x: ExpressionT) -> ExpressionT:
#         """Min a set of values.

#         Substrait: min
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def max(self, x: ExpressionT) -> ExpressionT:
#         """Max a set of values.

#         Substrait: max
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def product(self, x: ExpressionT, overflow: Any = None) -> ExpressionT:
#         """Product of a set of values. Returns 1 for empty input.

#         Substrait: product
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def std_dev(self, x: ExpressionT, rounding: Any = None, distribution: Any = None) -> ExpressionT:
#         """Calculates standard-deviation for a set of values.

#         Substrait: std_dev
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def variance(self, x: ExpressionT, rounding: Any = None, distribution: Any = None) -> ExpressionT:
#         """Calculates variance for a set of values.

#         Substrait: variance
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def corr(self, x: ExpressionT, y: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Calculates the value of Pearson's correlation coefficient between `x` and `y`. If there is no input, null is returned.


#         Substrait: corr
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def mode(self, x: ExpressionT) -> ExpressionT:
#         """Calculates mode for a set of values. If there is no input, null is returned.


#         Substrait: mode
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def median(self, precision: ExpressionT, x: ExpressionT, rounding: Any = None) -> ExpressionT:
#         """Calculate the median for a set of values.
# Returns null if applied to zero records. For the integer implementations, the rounding option determines how the median should be rounded if it ends up midway between two values. For the floating point implementations, they specify the usual floating point rounding mode.


#         Substrait: median
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
#         """
#         ...

#     def quantile(self, boundaries: ExpressionT, precision: ExpressionT, n: ExpressionT, distribution: ExpressionT, rounding: Any = None) -> ExpressionT:
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
