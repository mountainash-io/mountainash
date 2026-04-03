"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class SubstraitScalarRoundingDecimalExpressionSystemProtocol(Protocol):
    """Protocol for scalar rounding_decimal operations.

    Auto-generated from Substrait rounding_decimal extension.
    Function type: scalar
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

