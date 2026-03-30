"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union

from mountainash.core.types import ExpressionT


class SubstraitScalarRoundingExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for scalar rounding operations.

    Auto-generated from Substrait rounding extension.
    Function type: scalar
    """

    def ceil(self, x: ExpressionT, /) -> ExpressionT:
        """Rounding to the ceiling of the value `x`.


        Substrait: ceil
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...

    def floor(self, x: ExpressionT, /) -> ExpressionT:
        """Rounding to the floor of the value `x`.


        Substrait: floor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...

    def round(self, x: ExpressionT, /, s: int, rounding: Any = None) -> ExpressionT:
        """Rounding the value `x` to `s` decimal places.


        Substrait: round
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...
