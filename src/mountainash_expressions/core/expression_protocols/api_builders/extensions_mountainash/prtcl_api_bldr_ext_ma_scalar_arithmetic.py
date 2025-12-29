"""Mountainash arithmetic extension protocol.

Mountainash Extension: Arithmetic
URI: file://extensions/functions_arithmetic.yaml

Extensions beyond Substrait standard:
- floor_divide: Floor division (Python's //)
"""

from __future__ import annotations

from typing import Union, Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode


class MountainAshScalarArithmeticAPIBuilderProtocol(Protocol):
    """Builder protocol for arithmetic operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def floor_divide(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
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
