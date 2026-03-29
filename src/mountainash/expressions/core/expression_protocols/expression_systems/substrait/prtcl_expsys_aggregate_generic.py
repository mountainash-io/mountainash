"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

from mountainash.expressions.types import SupportedExpressions


if TYPE_CHECKING:
    from mountainash.expressions.types import SupportedExpressions

class SubstraitAggregateGenericExpressionSystemProtocol(Protocol):
    """Protocol for aggregate_generic operations.

    Auto-generated from Substrait aggregate_generic extension.
    """

    def count(self, x: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Count a set of values

        Substrait: count
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
        """
        ...

    def any_value(self, x: SupportedExpressions, /, ignore_nulls: Any = None) -> SupportedExpressions:
        """Selects an arbitrary value from a group of values.
If the input is empty, the function returns null.

        Substrait: any_value
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
        """
        ...
