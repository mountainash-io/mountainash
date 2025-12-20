"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace


class ScalarAggregateExpressionProtocol(Protocol):
    """Protocol for aggregate_generic operations.

    Auto-generated from Substrait aggregate_generic extension.
    """

    def count(self, x: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions:
        """Count a set of values

        Substrait: count
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_generic.yaml
        """
        ...

    def count_all(self, overflow: Any = None) -> SupportedExpressions:
        """Count a set of records (not field referenced)

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


class ScalarAggregateBuilderProtocol(Protocol):
    """Builder protocol for aggregate operations.

    Defines user-facing fluent API methods that create expression nodes.
    Note: Aggregate functions typically operate on grouped data.
    """

    def count(self) -> "BaseNamespace":
        """Count non-null values.

        Substrait: count
        """
        ...

    def any_value(self, ignore_nulls: bool = True) -> "BaseNamespace":
        """Select an arbitrary value from the group.

        Substrait: any_value
        """
        ...
