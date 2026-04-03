"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class SubstraitAggregateArithmeticDecimalExpressionSystemProtocol(Protocol):
    """Protocol for aggregate arithmetic_decimal operations.

    Auto-generated from Substrait arithmetic_decimal extension.
    Function type: aggregate
    """

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

