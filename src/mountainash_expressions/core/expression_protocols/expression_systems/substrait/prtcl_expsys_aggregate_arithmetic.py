"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class SubstraitAggregateArithmeticExpressionSystemProtocol(Protocol):
    """Protocol for aggregate arithmetic operations.

    Auto-generated from Substrait arithmetic extension.
    Function type: aggregate
    """

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
