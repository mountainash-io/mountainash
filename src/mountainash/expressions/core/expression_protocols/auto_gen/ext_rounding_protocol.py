"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol

# Placeholder - use your actual type
SupportedExpressions = Any



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
