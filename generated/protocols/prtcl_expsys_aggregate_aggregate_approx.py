"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions




class SubstraitAggregateAggregateApproxExpressionSystemProtocol(Protocol):
    """Protocol for aggregate aggregate_approx operations.

    Auto-generated from Substrait aggregate_approx extension.
    Function type: aggregate
    """

    def approx_count_distinct(self, x: SupportedExpressions) -> SupportedExpressions:
        """Calculates the approximate number of rows that contain distinct values of the expression argument using HyperLogLog. This function provides an alternative to the COUNT (DISTINCT expression) function, which returns the exact number of rows that contain distinct values of an expression. APPROX_COUNT_DISTINCT processes large amounts of data significantly faster than COUNT, with negligible deviation from the exact result.

        Substrait: approx_count_distinct
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_aggregate_approx.yaml
        """
        ...

