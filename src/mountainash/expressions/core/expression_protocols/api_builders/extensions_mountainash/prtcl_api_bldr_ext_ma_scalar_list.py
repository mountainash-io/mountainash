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

    def all(self) -> BaseExpressionAPI:
        """Check if all elements in each list are true."""
        ...

    def any(self) -> BaseExpressionAPI:
        """Check if any element in each list is true."""
        ...

    def drop_nulls(self) -> BaseExpressionAPI:
        """Remove null values from each list."""
        ...

    def median(self) -> BaseExpressionAPI:
        """Median of elements in each list."""
        ...

    def std(self, *, ddof: int = 1) -> BaseExpressionAPI:
        """Standard deviation of elements in each list."""
        ...

    def var(self, *, ddof: int = 1) -> BaseExpressionAPI:
        """Variance of elements in each list."""
        ...

    def n_unique(self) -> BaseExpressionAPI:
        """Count distinct elements in each list."""
        ...

    def count_matches(
        self,
        item: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Count occurrences of a value in each list."""
        ...

    def item(self, *, index: int = 0) -> BaseExpressionAPI:
        """Get element at the given index, returning null on out-of-bounds."""
        ...

    def reverse(self) -> BaseExpressionAPI:
        """Reverse each list."""
        ...

    def head(self, n: int = 5) -> BaseExpressionAPI:
        """Return the first n elements of each list."""
        ...

    def tail(self, n: int = 5) -> BaseExpressionAPI:
        """Return the last n elements of each list."""
        ...

    def slice(self, offset: int, *, length: int | None = None) -> BaseExpressionAPI:
        """Return a slice of each list."""
        ...

    def gather(self, indices: Any, *, null_on_oob: bool = False) -> BaseExpressionAPI:
        """Gather elements at the given indices."""
        ...

    def gather_every(self, n: int, *, offset: int = 0) -> BaseExpressionAPI:
        """Take every nth element of each list."""
        ...

    def shift(self, n: int) -> BaseExpressionAPI:
        """Shift list values by n positions."""
        ...

    def diff(self, *, n: int = 1, null_behavior: str = "ignore") -> BaseExpressionAPI:
        """Compute element-wise differences."""
        ...

    def set_union(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Union of two lists (deduplicated)."""
        ...

    def set_intersection(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Intersection of two lists (elements common to both)."""
        ...

    def set_difference(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Elements in self that are not in other."""
        ...

    def set_symmetric_difference(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Elements in either list but not both."""
        ...

    def concat(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Concatenate two lists."""
        ...

    def filter(self, mask: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Filter list elements by a boolean mask expression."""
        ...
