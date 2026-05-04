"""Mountainash list extension protocol.

Mountainash Extension: List Operations
URI: file://extensions/functions_list.yaml

Extensions beyond Substrait standard:
- List aggregation: sum, min, max, mean
- List inspection: len, contains
- List manipulation: sort, unique, explode, join, get
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode


class MountainAshScalarListAPIBuilderProtocol(Protocol):
    """Builder protocol for list operations.

    Defines user-facing fluent API methods for the .list namespace.
    """

    def sum(self) -> BaseExpressionAPI:
        """Sum all elements in each list."""
        ...

    def min(self) -> BaseExpressionAPI:
        """Minimum element in each list."""
        ...

    def max(self) -> BaseExpressionAPI:
        """Maximum element in each list."""
        ...

    def mean(self) -> BaseExpressionAPI:
        """Mean of elements in each list."""
        ...

    def len(self) -> BaseExpressionAPI:
        """Count of elements in each list."""
        ...

    def contains(
        self,
        item: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Check if each list contains the given item."""
        ...

    def sort(self, *, descending: bool = False) -> BaseExpressionAPI:
        """Sort elements in each list."""
        ...

    def unique(self) -> BaseExpressionAPI:
        """Distinct elements in each list."""
        ...

    def explode(self) -> BaseExpressionAPI:
        """Expand each list element into a separate row."""
        ...

    def join(self, separator: str = ",") -> BaseExpressionAPI:
        """Concatenate list elements into a single string."""
        ...

    def get(self, index: int) -> BaseExpressionAPI:
        """Get element at the given index."""
        ...

    def first(self) -> BaseExpressionAPI:
        """First element of each list."""
        ...

    def last(self) -> BaseExpressionAPI:
        """Last element of each list."""
        ...
