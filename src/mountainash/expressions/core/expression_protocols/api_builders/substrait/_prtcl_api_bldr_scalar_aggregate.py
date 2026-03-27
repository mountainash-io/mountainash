"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode


class SubstraitScalarAggregateAPIBuilderProtocol(Protocol):
    """Builder protocol for aggregate operations.

    Defines user-facing fluent API methods that create expression nodes.
    Note: Aggregate functions typically operate on grouped data.
    """

    def count(self) -> BaseExpressionAPI:
        """Count non-null values.

        Substrait: count
        """
        ...

    def any_value(self, ignore_nulls: bool = True) -> BaseExpressionAPI:
        """Select an arbitrary value from the group.

        Substrait: any_value
        """
        ...
