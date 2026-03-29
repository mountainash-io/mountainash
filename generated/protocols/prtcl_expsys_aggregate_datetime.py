"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class SubstraitAggregateDatetimeExpressionSystemProtocol(Protocol):
    """Protocol for aggregate datetime operations.

    Auto-generated from Substrait datetime extension.
    Function type: aggregate
    """

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

