"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class SubstraitAggregateAggregateGenericExpressionSystemProtocol(Protocol):
    """Protocol for aggregate aggregate_generic operations.

    Auto-generated from Substrait aggregate_generic extension.
    Function type: aggregate
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

