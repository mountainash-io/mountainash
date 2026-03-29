"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol

# Placeholder - use your actual type
SupportedExpressions = Any


class Aggregate_ApproxExpressionProtocol(Protocol):
    """Protocol for aggregate_approx operations.

    Auto-generated from Substrait aggregate_approx extension.
    """

    def approx_count_distinct(self, x: SupportedExpressions) -> SupportedExpressions:
        """Calculates the approximate number of rows that contain distinct values of the expression argument using HyperLogLog. This function provides an alternative to the COUNT (DISTINCT expression) function, which returns the exact number of rows that contain distinct values of an expression. APPROX_COUNT_DISTINCT processes large amounts of data significantly faster than COUNT, with negligible deviation from the exact result.

        Substrait: approx_count_distinct
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_approx.yaml
        """
        ...



class Aggregate_GenericExpressionProtocol(Protocol):
    """Protocol for aggregate_generic operations.

    Auto-generated from Substrait aggregate_generic extension.
    """

    def count(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Count a set of values

        Substrait: count
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
        """
        ...

    def count(self, overflow: Any = None) -> SupportedExpressions:
        """Count a set of records (not field referenced)

        Substrait: count
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
        """
        ...

    def any_value(self, x: SupportedExpressions, ignore_nulls: Any = None) -> SupportedExpressions:
        """Selects an arbitrary value from a group of values.
If the input is empty, the function returns null.


        Substrait: any_value
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
        """
        ...



class Aggregate_DecimalExpressionProtocol(Protocol):
    """Protocol for aggregate_decimal operations.

    Auto-generated from Substrait aggregate_decimal extension.
    """

    def count(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Count a set of values. Result is returned as a decimal instead of i64.

        Substrait: count
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_decimal_output.yaml
        """
        ...

    def count(self, overflow: Any = None) -> SupportedExpressions:
        """Count a set of records (not field referenced). Result is returned as a decimal instead of i64.

        Substrait: count
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_decimal_output.yaml
        """
        ...

    def approx_count_distinct(self, x: SupportedExpressions) -> SupportedExpressions:
        """Calculates the approximate number of rows that contain distinct values of the expression argument using HyperLogLog. This function provides an alternative to the COUNT (DISTINCT expression) function, which returns the exact number of rows that contain distinct values of an expression. APPROX_COUNT_DISTINCT processes large amounts of data significantly faster than COUNT, with negligible deviation from the exact result. Result is returned as a decimal instead of i64.

        Substrait: approx_count_distinct
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_decimal_output.yaml
        """
        ...



class ArithmeticExpressionProtocol(Protocol):
    """Protocol for arithmetic operations.

    Auto-generated from Substrait arithmetic extension.
    """

    def add(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Add two values.

        Substrait: add
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def subtract(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Subtract one value from another.

        Substrait: subtract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def multiply(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Multiply two values.

        Substrait: multiply
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def divide(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None, on_domain_error: Any = None, on_division_by_zero: Any = None) -> SupportedExpressions:
        """Divide x by y. In the case of integer division, partial values are truncated (i.e. rounded towards 0). The `on_division_by_zero` option governs behavior in cases where y is 0.  If the option is IEEE then the IEEE754 standard is followed: all values except +/-infinity return NaN and +/-infinity are unchanged. If the option is LIMIT then the result is +/-infinity in all cases. If either x or y are NaN then behavior will be governed by `on_domain_error`. If x and y are both +/-infinity, behavior will be governed by `on_domain_error`.


        Substrait: divide
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def negate(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Negation of the value

        Substrait: negate
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def modulus(self, x: SupportedExpressions, y: SupportedExpressions, division_type: Any = None, overflow: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
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

    def power(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Take the power with x as the base and y as exponent.

        Substrait: power
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sqrt(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
        """Square root of the value

        Substrait: sqrt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def exp(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """The mathematical constant e, raised to the power of the value.

        Substrait: exp
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def cos(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Get the cosine of a value in radians.

        Substrait: cos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sin(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Get the sine of a value in radians.

        Substrait: sin
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def tan(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Get the tangent of a value in radians.

        Substrait: tan
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def cosh(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Get the hyperbolic cosine of a value in radians.

        Substrait: cosh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sinh(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Get the hyperbolic sine of a value in radians.

        Substrait: sinh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def tanh(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Get the hyperbolic tangent of a value in radians.

        Substrait: tanh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def acos(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
        """Get the arccosine of a value in radians.

        Substrait: acos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def asin(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
        """Get the arcsine of a value in radians.

        Substrait: asin
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atan(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Get the arctangent of a value in radians.

        Substrait: atan
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def acosh(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
        """Get the hyperbolic arccosine of a value in radians.

        Substrait: acosh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def asinh(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Get the hyperbolic arcsine of a value in radians.

        Substrait: asinh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atanh(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
        """Get the hyperbolic arctangent of a value in radians.

        Substrait: atanh
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def atan2(self, x: SupportedExpressions, y: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None) -> SupportedExpressions:
        """Get the arctangent of values given as x/y pairs.

        Substrait: atan2
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def radians(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Converts angle `x` in degrees to radians.


        Substrait: radians
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def degrees(self, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Converts angle `x` in radians to degrees.


        Substrait: degrees
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def abs(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Calculate the absolute value of the argument.
Integer values allow the specification of overflow behavior to handle the unevenness of the twos complement, e.g. Int8 range [-128 : 127].


        Substrait: abs
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sign(self, x: SupportedExpressions) -> SupportedExpressions:
        """Return the signedness of the argument.
Integer values return signedness with the same type as the input. Possible return values are [-1, 0, 1]
Floating point values return signedness with the same type as the input. Possible return values are [-1.0, -0.0, 0.0, 1.0, NaN]


        Substrait: sign
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def factorial(self, n: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Return the factorial of a given integer input.
The factorial of 0! is 1 by convention.
Negative inputs will raise an error.


        Substrait: factorial
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_not(self, x: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise NOT result for one integer input.


        Substrait: bitwise_not
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_and(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise AND result for two integer inputs.


        Substrait: bitwise_and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_or(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise OR result for two given integer inputs.


        Substrait: bitwise_or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def bitwise_xor(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise XOR result for two integer inputs.


        Substrait: bitwise_xor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_left(self, base: SupportedExpressions, shift: SupportedExpressions) -> SupportedExpressions:
        """Bitwise shift left. The vacant (least-significant) bits are filled with zeros. Params:
  base – the base number to shift.
  shift – number of bits to left shift.

        Substrait: shift_left
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_right(self, base: SupportedExpressions, shift: SupportedExpressions) -> SupportedExpressions:
        """Bitwise (signed) shift right. The vacant (most-significant) bits are filled with zeros if the base number is positive or with ones if the base number is negative, thus preserving the sign of the resulting number. Params:
  base – the base number to shift.
  shift – number of bits to right shift.

        Substrait: shift_right
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def shift_right_unsigned(self, base: SupportedExpressions, shift: SupportedExpressions) -> SupportedExpressions:
        """Bitwise unsigned shift right. The vacant (most-significant) bits are filled with zeros. Params:
  base – the base number to shift.
  shift – number of bits to right shift.

        Substrait: shift_right_unsigned
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sum(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Sum a set of values. The sum of zero elements yields null.

        Substrait: sum
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def sum0(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Sum a set of values. The sum of zero elements yields zero.
Null values are ignored.


        Substrait: sum0
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def avg(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Average a set of values. For integral types, this truncates partial values.

        Substrait: avg
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def min(self, x: SupportedExpressions) -> SupportedExpressions:
        """Min a set of values.

        Substrait: min
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def max(self, x: SupportedExpressions) -> SupportedExpressions:
        """Max a set of values.

        Substrait: max
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def product(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Product of a set of values. Returns 1 for empty input.

        Substrait: product
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def std_dev(self, x: SupportedExpressions, rounding: Any = None, distribution: Any = None) -> SupportedExpressions:
        """Calculates standard-deviation for a set of values.

        Substrait: std_dev
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def variance(self, x: SupportedExpressions, rounding: Any = None, distribution: Any = None) -> SupportedExpressions:
        """Calculates variance for a set of values.

        Substrait: variance
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def corr(self, x: SupportedExpressions, y: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Calculates the value of Pearson's correlation coefficient between `x` and `y`. If there is no input, null is returned.


        Substrait: corr
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def mode(self, x: SupportedExpressions) -> SupportedExpressions:
        """Calculates mode for a set of values. If there is no input, null is returned.


        Substrait: mode
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def median(self, precision: SupportedExpressions, x: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Calculate the median for a set of values.
Returns null if applied to zero records. For the integer implementations, the rounding option determines how the median should be rounded if it ends up midway between two values. For the floating point implementations, they specify the usual floating point rounding mode.


        Substrait: median
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...

    def quantile(self, boundaries: SupportedExpressions, precision: SupportedExpressions, n: SupportedExpressions, distribution: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Calculates quantiles for a set of values.
This function will divide the aggregated values (passed via the distribution argument) over N equally-sized bins, where N is passed via a constant argument. It will then return the values at the boundaries of these bins in list form. If the input is appropriately sorted, this computes the quantiles of the distribution.
The function can optionally return the first and/or last element of the input, as specified by the `boundaries` argument. If the input is appropriately sorted, this will thus be the minimum and/or maximum values of the distribution.
When the boundaries do not lie exactly on elements of the incoming distribution, the function will interpolate between the two nearby elements. If the interpolated value cannot be represented exactly, the `rounding` option controls how the value should be selected or computed.
The function fails and returns null in the following cases:
  - `n` is null or less than one;
  - any value in `distribution` is null.

The function returns an empty list if `n` equals 1 and `boundaries` is set to `NEITHER`.


        Substrait: quantile
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic.yaml
        """
        ...



class Arithmetic_DecimalExpressionProtocol(Protocol):
    """Protocol for arithmetic_decimal operations.

    Auto-generated from Substrait arithmetic_decimal extension.
    """

    def add(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Add two decimal values.

        Substrait: add
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def subtract(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Substrait subtract function.

        Substrait: subtract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def multiply(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Substrait multiply function.

        Substrait: multiply
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def divide(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Substrait divide function.

        Substrait: divide
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def modulus(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Substrait modulus function.

        Substrait: modulus
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def abs(self, x: SupportedExpressions) -> SupportedExpressions:
        """Calculate the absolute value of the argument.

        Substrait: abs
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def bitwise_and(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise AND result for two decimal inputs. In inputs scale must be 0 (i.e. only integer types are allowed)


        Substrait: bitwise_and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def bitwise_or(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise OR result for two given decimal inputs. In inputs scale must be 0 (i.e. only integer types are allowed)


        Substrait: bitwise_or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def bitwise_xor(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Return the bitwise XOR result for two given decimal inputs. In inputs scale must be 0 (i.e. only integer types are allowed)


        Substrait: bitwise_xor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def sqrt(self, x: SupportedExpressions) -> SupportedExpressions:
        """Square root of the value. Sqrt of 0 is 0 and sqrt of negative values will raise an error.

        Substrait: sqrt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def factorial(self, n: SupportedExpressions) -> SupportedExpressions:
        """Return the factorial of a given decimal input. Scale should be 0 for factorial decimal input. The factorial of 0! is 1 by convention. Negative inputs will raise an error. Input which cause overflow of result will raise an error.


        Substrait: factorial
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def power(self, x: SupportedExpressions, y: SupportedExpressions, overflow: Any = None, complex_number_result: Any = None) -> SupportedExpressions:
        """Take the power with x as the base and y as exponent. Behavior for complex number result is indicated by option complex_number_result

        Substrait: power
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def sum(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Sum a set of values.

        Substrait: sum
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def avg(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Average a set of values.

        Substrait: avg
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def min(self, x: SupportedExpressions) -> SupportedExpressions:
        """Min a set of values.

        Substrait: min
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def max(self, x: SupportedExpressions) -> SupportedExpressions:
        """Max a set of values.

        Substrait: max
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...

    def sum0(self, x: SupportedExpressions, overflow: Any = None) -> SupportedExpressions:
        """Sum a set of values. The sum of zero elements yields zero.
Null values are ignored.


        Substrait: sum0
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_arithmetic_decimal.yaml
        """
        ...



class BooleanExpressionProtocol(Protocol):
    """Protocol for boolean operations.

    Auto-generated from Substrait boolean extension.
    """

    def or_(self, a: SupportedExpressions) -> SupportedExpressions:
        """The boolean `or` using Kleene logic.
This function behaves as follows with nulls:

    true or null = true

    null or true = true

    false or null = null

    null or false = null

    null or null = null

In other words, in this context a null value really means "unknown", and an unknown value `or` true is always true.
Behavior for 0 or 1 inputs is as follows:
  or() -> false
  or(x) -> x


        Substrait: or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def and_(self, a: SupportedExpressions) -> SupportedExpressions:
        """The boolean `and` using Kleene logic.
This function behaves as follows with nulls:

    true and null = null

    null and true = null

    false and null = false

    null and false = false

    null and null = null

In other words, in this context a null value really means "unknown", and an unknown value `and` false is always false.
Behavior for 0 or 1 inputs is as follows:
  and() -> true
  and(x) -> x


        Substrait: and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def and_not(self, a: SupportedExpressions, b: SupportedExpressions) -> SupportedExpressions:
        """The boolean `and` of one value and the negation of the other using Kleene logic.
This function behaves as follows with nulls:

    true and not null = null

    null and not false = null

    false and not null = false

    null and not true = false

    null and not null = null

In other words, in this context a null value really means "unknown", and an unknown value `and not` true is always false, as is false `and not` an unknown value.


        Substrait: and_not
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def xor(self, a: SupportedExpressions, b: SupportedExpressions) -> SupportedExpressions:
        """The boolean `xor` of two values using Kleene logic.
When a null is encountered in either input, a null is output.


        Substrait: xor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def not_(self, a: SupportedExpressions) -> SupportedExpressions:
        """The `not` of a boolean value.
When a null is input, a null is output.


        Substrait: not
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def bool_and(self, a: SupportedExpressions) -> SupportedExpressions:
        """If any value in the input is false, false is returned. If the input is empty or only contains nulls, null is returned. Otherwise, true is returned.


        Substrait: bool_and
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...

    def bool_or(self, a: SupportedExpressions) -> SupportedExpressions:
        """If any value in the input is true, true is returned. If the input is empty or only contains nulls, null is returned. Otherwise, false is returned.


        Substrait: bool_or
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_boolean.yaml
        """
        ...



class ComparisonExpressionProtocol(Protocol):
    """Protocol for comparison operations.

    Auto-generated from Substrait comparison extension.
    """

    def not_equal(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Whether two values are not_equal.
`not_equal(x, y) := (x != y)`
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: not_equal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def equal(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Whether two values are equal.
`equal(x, y) := (x == y)`
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: equal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_not_distinct_from(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Whether two values are equal.
This function treats `null` values as comparable, so
`is_not_distinct_from(null, null) == True`
This is in contrast to `equal`, in which `null` values do not compare.


        Substrait: is_not_distinct_from
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_distinct_from(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Whether two values are not equal.
This function treats `null` values as comparable, so
`is_distinct_from(null, null) == False`
This is in contrast to `equal`, in which `null` values do not compare.


        Substrait: is_distinct_from
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def lt(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Less than.
lt(x, y) := (x < y)
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: lt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def gt(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Greater than.
gt(x, y) := (x > y)
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: gt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def lte(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Less than or equal to.
lte(x, y) := (x <= y)
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: lte
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def gte(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Greater than or equal to.
gte(x, y) := (x >= y)
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: gte
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def between(self, expression: SupportedExpressions, low: SupportedExpressions, high: SupportedExpressions) -> SupportedExpressions:
        """Whether the `expression` is greater than or equal to `low` and less than or equal to `high`.
`expression` BETWEEN `low` AND `high`
If `low`, `high`, or `expression` are `null`, `null` is returned.

        Substrait: between
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_true(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is true.

        Substrait: is_true
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_not_true(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is not true.

        Substrait: is_not_true
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_false(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is false.

        Substrait: is_false
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_not_false(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is not false.

        Substrait: is_not_false
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_null(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is null. NaN is not null.

        Substrait: is_null
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_not_null(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is not null. NaN is not null.

        Substrait: is_not_null
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_nan(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is not a number.
If `x` is `null`, `null` is returned.


        Substrait: is_nan
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_finite(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is finite (neither infinite nor NaN).
If `x` is `null`, `null` is returned.


        Substrait: is_finite
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_infinite(self, x: SupportedExpressions) -> SupportedExpressions:
        """Whether a value is infinite.
If `x` is `null`, `null` is returned.


        Substrait: is_infinite
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def nullif(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """If two values are equal, return null. Otherwise, return the first value.

        Substrait: nullif
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def coalesce(self, arg: SupportedExpressions) -> SupportedExpressions:
        """Evaluate arguments from left to right and return the first argument that is not null. Once a non-null argument is found, the remaining arguments are not evaluated.
If all arguments are null, return null.

        Substrait: coalesce
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def least(self, arg: SupportedExpressions) -> SupportedExpressions:
        """Evaluates each argument and returns the smallest one. The function will return null if any argument evaluates to null.

        Substrait: least
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def least_skip_null(self, arg: SupportedExpressions) -> SupportedExpressions:
        """Evaluates each argument and returns the smallest one. The function will return null only if all arguments evaluate to null.

        Substrait: least_skip_null
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def greatest(self, arg: SupportedExpressions) -> SupportedExpressions:
        """Evaluates each argument and returns the largest one. The function will return null if any argument evaluates to null.

        Substrait: greatest
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def greatest_skip_null(self, arg: SupportedExpressions) -> SupportedExpressions:
        """Evaluates each argument and returns the largest one. The function will return null only if all arguments evaluate to null.

        Substrait: greatest_skip_null
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...



class DatetimeExpressionProtocol(Protocol):
    """Protocol for datetime operations.

    Auto-generated from Substrait datetime extension.
    """

    def extract(self, component: SupportedExpressions, x: SupportedExpressions, timezone: SupportedExpressions) -> SupportedExpressions:
        """Extract portion of a date/time value. * YEAR Return the year. * ISO_YEAR Return the ISO 8601 week-numbering year. First week of an ISO year has the majority (4 or more) of
  its days in January.
* US_YEAR Return the US epidemiological year. First week of US epidemiological year has the majority (4 or more)
  of its days in January. Last week of US epidemiological year has the year's last Wednesday in it. US
  epidemiological week starts on Sunday.
* QUARTER Return the number of the quarter within the year. January 1 through March 31 map to the first quarter,
  April 1 through June 30 map to the second quarter, etc.
* MONTH Return the number of the month within the year. * DAY Return the number of the day within the month. * DAY_OF_YEAR Return the number of the day within the year. January 1 maps to the first day, February 1 maps to
  the thirty-second day, etc.
* MONDAY_DAY_OF_WEEK Return the number of the day within the week, from Monday (first day) to Sunday (seventh
  day).
* SUNDAY_DAY_OF_WEEK Return the number of the day within the week, from Sunday (first day) to Saturday (seventh
  day).
* MONDAY_WEEK Return the number of the week within the year. First week starts on first Monday of January. * SUNDAY_WEEK Return the number of the week within the year. First week starts on first Sunday of January. * ISO_WEEK Return the number of the ISO week within the ISO year. First ISO week has the majority (4 or more)
  of its days in January. ISO week starts on Monday.
* US_WEEK Return the number of the US week within the US year. First US week has the majority (4 or more) of
  its days in January. US week starts on Sunday.
* HOUR Return the hour (0-23). * MINUTE Return the minute (0-59). * SECOND Return the second (0-59). * MILLISECOND Return number of milliseconds since the last full second. * MICROSECOND Return number of microseconds since the last full millisecond. * NANOSECOND Return number of nanoseconds since the last full microsecond. * PICOSECOND Return number of picoseconds since the last full nanosecond. * SUBSECOND Return number of microseconds since the last full second of the given timestamp. * UNIX_TIME Return number of seconds that have elapsed since 1970-01-01 00:00:00 UTC, ignoring leap seconds. * TIMEZONE_OFFSET Return number of seconds of timezone offset to UTC.
The range of values returned for QUARTER, MONTH, DAY, DAY_OF_YEAR, MONDAY_DAY_OF_WEEK, SUNDAY_DAY_OF_WEEK, MONDAY_WEEK, SUNDAY_WEEK, ISO_WEEK, and US_WEEK depends on whether counting starts at 1 or 0. This is governed by the indexing option.
When indexing is ONE: * QUARTER returns values in range 1-4 * MONTH returns values in range 1-12 * DAY returns values in range 1-31 * DAY_OF_YEAR returns values in range 1-366 * MONDAY_DAY_OF_WEEK and SUNDAY_DAY_OF_WEEK return values in range 1-7 * MONDAY_WEEK, SUNDAY_WEEK, ISO_WEEK, and US_WEEK return values in range 1-53
When indexing is ZERO: * QUARTER returns values in range 0-3 * MONTH returns values in range 0-11 * DAY returns values in range 0-30 * DAY_OF_YEAR returns values in range 0-365 * MONDAY_DAY_OF_WEEK and SUNDAY_DAY_OF_WEEK return values in range 0-6 * MONDAY_WEEK, SUNDAY_WEEK, ISO_WEEK, and US_WEEK return values in range 0-52
The indexing option must be specified when the component is QUARTER, MONTH, DAY, DAY_OF_YEAR, MONDAY_DAY_OF_WEEK, SUNDAY_DAY_OF_WEEK, MONDAY_WEEK, SUNDAY_WEEK, ISO_WEEK, or US_WEEK. The indexing option cannot be specified when the component is YEAR, ISO_YEAR, US_YEAR, HOUR, MINUTE, SECOND, MILLISECOND, MICROSECOND, SUBSECOND, UNIX_TIME, or TIMEZONE_OFFSET.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: extract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def extract_boolean(self, component: SupportedExpressions, x: SupportedExpressions) -> SupportedExpressions:
        """Extract boolean values of a date/time value. * IS_LEAP_YEAR Return true if year of the given value is a leap year and false otherwise. * IS_DST Return true if DST (Daylight Savings Time) is observed at the given value
  in the given timezone.

Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: extract_boolean
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def add(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Add an interval to a date/time type.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: add
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def multiply(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Multiply an interval by an integral number.

        Substrait: multiply
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def add_intervals(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Add two intervals together.

        Substrait: add_intervals
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def subtract(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Subtract an interval from a date/time type.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: subtract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def lte(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """less than or equal to

        Substrait: lte
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def lt(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """less than

        Substrait: lt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def gte(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """greater than or equal to

        Substrait: gte
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def gt(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """greater than

        Substrait: gt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def assume_timezone(self, x: SupportedExpressions, timezone: SupportedExpressions) -> SupportedExpressions:
        """Convert local timestamp to UTC-relative timestamp_tz using given local time's timezone.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: assume_timezone
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def local_timestamp(self, x: SupportedExpressions, timezone: SupportedExpressions) -> SupportedExpressions:
        """Convert UTC-relative timestamp_tz to local timestamp using given local time's timezone.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: local_timestamp
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def strptime_time(self, time_string: SupportedExpressions, format: SupportedExpressions) -> SupportedExpressions:
        """Parse string into time using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference.

        Substrait: strptime_time
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def strptime_date(self, date_string: SupportedExpressions, format: SupportedExpressions) -> SupportedExpressions:
        """Parse string into date using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference.

        Substrait: strptime_date
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def strptime_timestamp(self, timestamp_string: SupportedExpressions, format: SupportedExpressions, timezone: SupportedExpressions) -> SupportedExpressions:
        """Parse string into timestamp using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference. If timezone is present in timestamp and provided as parameter an error is thrown.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is supplied as parameter and present in the parsed string the parsed timezone is used. If parameter supplied timezone is invalid an error is thrown.

        Substrait: strptime_timestamp
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def strftime(self, x: SupportedExpressions, format: SupportedExpressions) -> SupportedExpressions:
        """Convert timestamp/date/time to string using provided format, see https://man7.org/linux/man-pages/man3/strftime.3.html for reference.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: strftime
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def round_temporal(self, x: SupportedExpressions, rounding: SupportedExpressions, unit: SupportedExpressions, multiple: SupportedExpressions, origin: SupportedExpressions) -> SupportedExpressions:
        """Round a given timestamp/date/time to a multiple of a time unit. If the given timestamp is not already an exact multiple from the origin in the given timezone, the resulting point is chosen as one of the two nearest multiples. Which of these is chosen is governed by rounding: FLOOR means to use the earlier one, CEIL means to use the later one, ROUND_TIE_DOWN means to choose the nearest and tie to the earlier one if equidistant, ROUND_TIE_UP means to choose the nearest and tie to the later one if equidistant.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: round_temporal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def round_calendar(self, x: SupportedExpressions, rounding: SupportedExpressions, unit: SupportedExpressions, origin: SupportedExpressions, multiple: SupportedExpressions) -> SupportedExpressions:
        """Round a given timestamp/date/time to a multiple of a time unit. If the given timestamp is not already an exact multiple from the last origin unit in the given timezone, the resulting point is chosen as one of the two nearest multiples. Which of these is chosen is governed by rounding: FLOOR means to use the earlier one, CEIL means to use the later one, ROUND_TIE_DOWN means to choose the nearest and tie to the earlier one if equidistant, ROUND_TIE_UP means to choose the nearest and tie to the later one if equidistant.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: round_calendar
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def min(self, x: SupportedExpressions) -> SupportedExpressions:
        """Min a set of values.

        Substrait: min
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def max(self, x: SupportedExpressions) -> SupportedExpressions:
        """Max a set of values.

        Substrait: max
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...



class GeometryExpressionProtocol(Protocol):
    """Protocol for geometry operations.

    Auto-generated from Substrait geometry extension.
    """

    def point(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
        """Returns a 2D point with the given `x` and `y` coordinate values.


        Substrait: point
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def make_line(self, geom1: SupportedExpressions, geom2: SupportedExpressions) -> SupportedExpressions:
        """Returns a linestring connecting the endpoint of geometry `geom1` to the begin point of geometry `geom2`. Repeated points at the beginning of input geometries are collapsed to a single point.
A linestring can be closed or simple.  A closed linestring starts and ends on the same point. A simple linestring does not cross or touch itself.


        Substrait: make_line
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def x_coordinate(self, point: SupportedExpressions) -> SupportedExpressions:
        """Return the x coordinate of the point.  Return null if not available.


        Substrait: x_coordinate
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def y_coordinate(self, point: SupportedExpressions) -> SupportedExpressions:
        """Return the y coordinate of the point.  Return null if not available.


        Substrait: y_coordinate
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def num_points(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return the number of points in the geometry.  The geometry should be an linestring or circularstring.


        Substrait: num_points
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_empty(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return true is the geometry is an empty geometry.


        Substrait: is_empty
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_closed(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return true if the geometry's start and end points are the same.


        Substrait: is_closed
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_simple(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return true if the geometry does not self intersect.


        Substrait: is_simple
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_ring(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return true if the geometry's start and end points are the same and it does not self intersect.


        Substrait: is_ring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def geometry_type(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return the type of geometry as a string.


        Substrait: geometry_type
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def envelope(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return the minimum bounding box for the input geometry as a geometry.
The returned geometry is defined by the corner points of the bounding box.  If the input geometry is a point or a line, the returned geometry can also be a point or line.


        Substrait: envelope
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def dimension(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return the dimension of the input geometry.  If the input is a collection of geometries, return the largest dimension from the collection. Dimensionality is determined by the complexity of the input and not the coordinate system being used.
Type dimensions: POINT   - 0 LINE    - 1 POLYGON - 2


        Substrait: dimension
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def is_valid(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return true if the input geometry is a valid 2D geometry.
For 3 dimensional and 4 dimensional geometries, the validity is still only tested in 2 dimensions.


        Substrait: is_valid
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def collection_extract(self, geom_collection: SupportedExpressions) -> SupportedExpressions:
        """Given the input geometry collection, return a homogenous multi-geometry.  All geometries in the multi-geometry will have the same dimension.
If type is not specified, the multi-geometry will only contain geometries of the highest dimension.  If type is specified, the multi-geometry will only contain geometries of that type.  If there are no geometries of the specified type, an empty geometry is returned.  Only points, linestrings, and polygons are supported.
Type numbers: POINT   - 0 LINE    - 1 POLYGON - 2


        Substrait: collection_extract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def flip_coordinates(self, geom_collection: SupportedExpressions) -> SupportedExpressions:
        """Return a version of the input geometry with the X and Y axis flipped.
This operation can be performed on geometries with more than 2 dimensions. However, only X and Y axis will be flipped.


        Substrait: flip_coordinates
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def remove_repeated_points(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return a version of the input geometry with duplicate consecutive points removed.
If the `tolerance` argument is provided, consecutive points within the tolerance distance of one another are considered to be duplicates.


        Substrait: remove_repeated_points
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def buffer(self, geom: SupportedExpressions, buffer_radius: SupportedExpressions) -> SupportedExpressions:
        """Compute and return an expanded version of the input geometry. All the points of the returned geometry are at a distance of `buffer_radius` away from the points of the input geometry. If a negative `buffer_radius` is provided, the geometry will shrink instead of expand.  A negative `buffer_radius` may shrink the geometry completely, in which case an empty geometry is returned. For input the geometries of points or lines, a negative `buffer_radius` will always return an emtpy geometry.


        Substrait: buffer
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def centroid(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return a point which is the geometric center of mass of the input geometry.


        Substrait: centroid
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...

    def minimum_bounding_circle(self, geom: SupportedExpressions) -> SupportedExpressions:
        """Return the smallest circle polygon that contains the input geometry.


        Substrait: minimum_bounding_circle
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_geometry.yaml
        """
        ...



class LogarithmicExpressionProtocol(Protocol):
    """Protocol for logarithmic operations.

    Auto-generated from Substrait logarithmic extension.
    """

    def ln(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Natural logarithm of the value

        Substrait: ln
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log10(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm to base 10 of the value

        Substrait: log10
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log2(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm to base 2 of the value

        Substrait: log2
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def logb(self, x: SupportedExpressions, base: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Logarithm of the value with the given base
logb(x, b) => log_{b} (x)


        Substrait: logb
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...

    def log1p(self, x: SupportedExpressions, rounding: Any = None, on_domain_error: Any = None, on_log_zero: Any = None) -> SupportedExpressions:
        """Natural logarithm (base e) of 1 + x
log1p(x) => log(1+x)


        Substrait: log1p
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_logarithmic.yaml
        """
        ...



class RoundingExpressionProtocol(Protocol):
    """Protocol for rounding operations.

    Auto-generated from Substrait rounding extension.
    """

    def ceil(self, x: SupportedExpressions) -> SupportedExpressions:
        """Rounding to the ceiling of the value `x`.


        Substrait: ceil
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...

    def floor(self, x: SupportedExpressions) -> SupportedExpressions:
        """Rounding to the floor of the value `x`.


        Substrait: floor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...

    def round(self, x: SupportedExpressions, s: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Rounding the value `x` to `s` decimal places.


        Substrait: round
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...



class Rounding_DecimalExpressionProtocol(Protocol):
    """Protocol for rounding_decimal operations.

    Auto-generated from Substrait rounding_decimal extension.
    """

    def ceil(self, x: SupportedExpressions) -> SupportedExpressions:
        """Rounding to the ceiling of the value `x`.


        Substrait: ceil
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding_decimal.yaml
        """
        ...

    def floor(self, x: SupportedExpressions) -> SupportedExpressions:
        """Rounding to the floor of the value `x`.


        Substrait: floor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding_decimal.yaml
        """
        ...

    def round(self, x: SupportedExpressions, s: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Rounding the value `x` to `s` decimal places.


        Substrait: round
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding_decimal.yaml
        """
        ...



class SetExpressionProtocol(Protocol):
    """Protocol for set operations.

    Auto-generated from Substrait set extension.
    """

    def index_in(self, needle: SupportedExpressions, haystack: SupportedExpressions, nan_equality: Any = None) -> SupportedExpressions:
        """Checks the membership of a value in a list of values
Returns the first 0-based index value of some input `needle` if `needle` is equal to any element in `haystack`.  Returns `NULL` if not found.
If `needle` is `NULL`, returns `NULL`.
If `needle` is `NaN`:
  - Returns 0-based index of `NaN` in `input` (default)
  - Returns `NULL` (if `NAN_IS_NOT_NAN` is specified)


        Substrait: index_in
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_set.yaml
        """
        ...



class StringExpressionProtocol(Protocol):
    """Protocol for string operations.

    Auto-generated from Substrait string extension.
    """

    def concat(self, input: SupportedExpressions, null_handling: Any = None) -> SupportedExpressions:
        """Concatenate strings.
The `null_handling` option determines whether or not null values will be recognized by the function. If `null_handling` is set to `IGNORE_NULLS`, null value arguments will be ignored when strings are concatenated. If set to `ACCEPT_NULLS`, the result will be null if any argument passed to the concat function is null.

        Substrait: concat
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def like(self, input: SupportedExpressions, match: SupportedExpressions, case_sensitivity: Any = None) -> SupportedExpressions:
        """Are two strings like each other.
The `case_sensitivity` option applies to the `match` argument.

        Substrait: like
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def substring(self, input: SupportedExpressions, start: SupportedExpressions, length: SupportedExpressions, negative_start: Any = None) -> SupportedExpressions:
        """Extract a substring of a specified `length` starting from position `start`. A `start` value of 1 refers to the first characters of the string.  When `length` is not specified the function will extract a substring starting from position `start` and ending at the end of the string.
The `negative_start` option applies to the `start` parameter. `WRAP_FROM_END` means the index will start from the end of the `input` and move backwards. The last character has an index of -1, the second to last character has an index of -2, and so on. `LEFT_OF_BEGINNING` means the returned substring will start from the left of the first character.  A `start` of -1 will begin 2 characters left of the the `input`, while a `start` of 0 begins 1 character left of the `input`.

        Substrait: substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_match_substring(self, input: SupportedExpressions, pattern: SupportedExpressions, position: SupportedExpressions, occurrence: SupportedExpressions, group: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Extract a substring that matches the given regular expression pattern. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The occurrence of the pattern to be extracted is specified using the `occurrence` argument. Specifying `1` means the first occurrence will be extracted, `2` means the second occurrence, and so on. The `occurrence` argument should be a positive non-zero integer. The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer. The regular expression capture group can be specified using the `group` argument. Specifying `0` will return the substring matching the full regular expression. Specifying `1` will return the substring matching only the first capture group, and so on. The `group` argument should be a non-negative integer.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile, the occurrence value is out of range, the position value is out of range, or the group value is out of range.

        Substrait: regexp_match_substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_match_substring(self, input: SupportedExpressions, pattern: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Extract a substring that matches the given regular expression pattern. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The first occurrence of the pattern from the beginning of the string is extracted. It returns the substring matching the full regular expression.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile.

        Substrait: regexp_match_substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_match_substring_all(self, input: SupportedExpressions, pattern: SupportedExpressions, position: SupportedExpressions, group: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Extract all substrings that match the given regular expression pattern. This will return a list of extracted strings with one value for each occurrence of a match. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer. The regular expression capture group can be specified using the `group` argument. Specifying `0` will return substrings matching the full regular expression. Specifying `1` will return substrings matching only the first capture group, and so on. The `group` argument should be a non-negative integer.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile, the position value is out of range, or the group value is out of range.

        Substrait: regexp_match_substring_all
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def starts_with(self, input: SupportedExpressions, substring: SupportedExpressions, case_sensitivity: Any = None) -> SupportedExpressions:
        """Whether the `input` string starts with the `substring`.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: starts_with
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def ends_with(self, input: SupportedExpressions, substring: SupportedExpressions, case_sensitivity: Any = None) -> SupportedExpressions:
        """Whether `input` string ends with the substring.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: ends_with
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def contains(self, input: SupportedExpressions, substring: SupportedExpressions, case_sensitivity: Any = None) -> SupportedExpressions:
        """Whether the `input` string contains the `substring`.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: contains
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def strpos(self, input: SupportedExpressions, substring: SupportedExpressions, case_sensitivity: Any = None) -> SupportedExpressions:
        """Return the position of the first occurrence of a string in another string. The first character of the string is at position 1. If no occurrence is found, 0 is returned.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: strpos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_strpos(self, input: SupportedExpressions, pattern: SupportedExpressions, position: SupportedExpressions, occurrence: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Return the position of an occurrence of the given regular expression pattern in a string. The first character of the string is at position 1. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer. Which occurrence to return the position of is specified using the `occurrence` argument. Specifying `1` means the position first occurrence will be returned, `2` means the position of the second occurrence, and so on. The `occurrence` argument should be a positive non-zero integer. If no occurrence is found, 0 is returned.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile, the occurrence value is out of range, or the position value is out of range.

        Substrait: regexp_strpos
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def count_substring(self, input: SupportedExpressions, substring: SupportedExpressions, case_sensitivity: Any = None) -> SupportedExpressions:
        """Return the number of non-overlapping occurrences of a substring in an input string.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: count_substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_count_substring(self, input: SupportedExpressions, pattern: SupportedExpressions, position: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Return the number of non-overlapping occurrences of a regular expression pattern in an input string. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile or the position value is out of range.

        Substrait: regexp_count_substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_count_substring(self, input: SupportedExpressions, pattern: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Return the number of non-overlapping occurrences of a regular expression pattern in an input string. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html). The match starts at the first character of the input string.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile.

        Substrait: regexp_count_substring
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def replace(self, input: SupportedExpressions, substring: SupportedExpressions, replacement: SupportedExpressions, case_sensitivity: Any = None) -> SupportedExpressions:
        """Replace all occurrences of the substring with the replacement string.
The `case_sensitivity` option applies to the `substring` argument.

        Substrait: replace
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def concat_ws(self, separator: SupportedExpressions, string_arguments: SupportedExpressions) -> SupportedExpressions:
        """Concatenate strings together separated by a separator.

        Substrait: concat_ws
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def repeat(self, input: SupportedExpressions, count: SupportedExpressions) -> SupportedExpressions:
        """Repeat a string `count` number of times.

        Substrait: repeat
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def reverse(self, input: SupportedExpressions) -> SupportedExpressions:
        """Returns the string in reverse order.

        Substrait: reverse
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def replace_slice(self, input: SupportedExpressions, start: SupportedExpressions, length: SupportedExpressions, replacement: SupportedExpressions) -> SupportedExpressions:
        """Replace a slice of the input string.  A specified 'length' of characters will be deleted from the input string beginning at the 'start' position and will be replaced by a new string.  A start value of 1 indicates the first character of the input string. If start is negative or zero, or greater than the length of the input string, a null string is returned. If 'length' is negative, a null string is returned.  If 'length' is zero, inserting of the new string occurs at the specified 'start' position and no characters are deleted. If 'length' is greater than the input string, deletion will occur up to the last character of the input string.

        Substrait: replace_slice
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def lower(self, input: SupportedExpressions, char_set: Any = None) -> SupportedExpressions:
        """Transform the string to lower case characters. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: lower
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def upper(self, input: SupportedExpressions, char_set: Any = None) -> SupportedExpressions:
        """Transform the string to upper case characters. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: upper
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def swapcase(self, input: SupportedExpressions, char_set: Any = None) -> SupportedExpressions:
        """Transform the string's lowercase characters to uppercase and uppercase characters to lowercase. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: swapcase
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def capitalize(self, input: SupportedExpressions, char_set: Any = None) -> SupportedExpressions:
        """Capitalize the first character of the input string. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: capitalize
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def title(self, input: SupportedExpressions, char_set: Any = None) -> SupportedExpressions:
        """Converts the input string into titlecase. Capitalize the first character of each word in the input string except for articles (a, an, the). Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: title
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def initcap(self, input: SupportedExpressions, char_set: Any = None) -> SupportedExpressions:
        """Capitalizes the first character of each word in the input string, including articles, and lowercases the rest. Implementation should follow the utf8_unicode_ci collations according to the Unicode Collation Algorithm described at http://www.unicode.org/reports/tr10/.

        Substrait: initcap
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def char_length(self, input: SupportedExpressions) -> SupportedExpressions:
        """Return the number of characters in the input string.  The length includes trailing spaces.

        Substrait: char_length
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def bit_length(self, input: SupportedExpressions) -> SupportedExpressions:
        """Return the number of bits in the input string.

        Substrait: bit_length
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def octet_length(self, input: SupportedExpressions) -> SupportedExpressions:
        """Return the number of bytes in the input string.

        Substrait: octet_length
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_replace(self, input: SupportedExpressions, pattern: SupportedExpressions, replacement: SupportedExpressions, position: SupportedExpressions, occurrence: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Search a string for a substring that matches a given regular expression pattern and replace it with a replacement string. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github .io/icu/userguide/strings/regexp.html). The occurrence of the pattern to be replaced is specified using the `occurrence` argument. Specifying `1` means only the first occurrence will be replaced, `2` means the second occurrence, and so on. Specifying `0` means all occurrences will be replaced. The number of characters from the beginning of the string to begin starting to search for pattern matches can be specified using the `position` argument. Specifying `1` means to search for matches starting at the first character of the input string, `2` means the second character, and so on. The `position` argument should be a positive non-zero integer. The replacement string can capture groups using numbered backreferences.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines.  This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile, the replacement contains an illegal back-reference, the occurrence value is out of range, or the position value is out of range.

        Substrait: regexp_replace
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_replace(self, input: SupportedExpressions, pattern: SupportedExpressions, replacement: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Search a string for a substring that matches a given regular expression pattern and replace it with a replacement string. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github .io/icu/userguide/strings/regexp.html). The replacement string can capture groups using numbered backreferences. All occurrences of the pattern will be replaced. The search for matches start at the first character of the input.
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines.  This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.
Behavior is undefined if the regex fails to compile or the replacement contains an illegal back-reference.

        Substrait: regexp_replace
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def ltrim(self, input: SupportedExpressions, characters: SupportedExpressions) -> SupportedExpressions:
        """Remove any occurrence of the characters from the left side of the string. If no characters are specified, spaces are removed.

        Substrait: ltrim
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def rtrim(self, input: SupportedExpressions, characters: SupportedExpressions) -> SupportedExpressions:
        """Remove any occurrence of the characters from the right side of the string. If no characters are specified, spaces are removed.

        Substrait: rtrim
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def trim(self, input: SupportedExpressions, characters: SupportedExpressions) -> SupportedExpressions:
        """Remove any occurrence of the characters from the left and right sides of the string. If no characters are specified, spaces are removed.

        Substrait: trim
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def lpad(self, input: SupportedExpressions, length: SupportedExpressions, characters: SupportedExpressions) -> SupportedExpressions:
        """Left-pad the input string with the string of 'characters' until the specified length of the string has been reached. If the input string is longer than 'length', remove characters from the right-side to shorten it to 'length' characters. If the string of 'characters' is longer than the remaining 'length' needed to be filled, only pad until 'length' has been reached. If 'characters' is not specified, the default value is a single space.

        Substrait: lpad
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def rpad(self, input: SupportedExpressions, length: SupportedExpressions, characters: SupportedExpressions) -> SupportedExpressions:
        """Right-pad the input string with the string of 'characters' until the specified length of the string has been reached. If the input string is longer than 'length', remove characters from the left-side to shorten it to 'length' characters. If the string of 'characters' is longer than the remaining 'length' needed to be filled, only pad until 'length' has been reached. If 'characters' is not specified, the default value is a single space.

        Substrait: rpad
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def center(self, input: SupportedExpressions, length: SupportedExpressions, character: SupportedExpressions, padding: Any = None) -> SupportedExpressions:
        """Center the input string by padding the sides with a single `character` until the specified `length` of the string has been reached. By default, if the `length` will be reached with an uneven number of padding, the extra padding will be applied to the right side. The side with extra padding can be controlled with the `padding` option.
Behavior is undefined if the number of characters passed to the `character` argument is not 1.

        Substrait: center
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def left(self, input: SupportedExpressions, count: SupportedExpressions) -> SupportedExpressions:
        """Extract `count` characters starting from the left of the string.

        Substrait: left
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def right(self, input: SupportedExpressions, count: SupportedExpressions) -> SupportedExpressions:
        """Extract `count` characters starting from the right of the string.

        Substrait: right
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def string_split(self, input: SupportedExpressions, separator: SupportedExpressions) -> SupportedExpressions:
        """Split a string into a list of strings, based on a specified `separator` character.

        Substrait: string_split
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def regexp_string_split(self, input: SupportedExpressions, pattern: SupportedExpressions, case_sensitivity: Any = None, multiline: Any = None, dotall: Any = None) -> SupportedExpressions:
        """Split a string into a list of strings, based on a regular expression pattern.  The substrings matched by the pattern will be used as the separators to split the input string and will not be included in the resulting list. The regular expression pattern should follow the International Components for Unicode implementation (https://unicode-org.github.io/icu/userguide/strings/regexp.html).
The `case_sensitivity` option specifies case-sensitive or case-insensitive matching. Enabling the `multiline` option will treat the input string as multiple lines. This makes the `^` and `$` characters match at the beginning and end of any line, instead of just the beginning and end of the input string. Enabling the `dotall` option makes the `.` character match line terminator characters in a string.

        Substrait: regexp_string_split
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

    def string_agg(self, input: SupportedExpressions, separator: SupportedExpressions) -> SupportedExpressions:
        """Concatenates a column of string values with a separator.

        Substrait: string_agg
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_string.yaml
        """
        ...

