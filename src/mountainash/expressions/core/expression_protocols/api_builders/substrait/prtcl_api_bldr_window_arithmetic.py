"""Substrait window arithmetic API builder protocol.

Substrait Extension: Window Arithmetic
URI: /extensions/functions_arithmetic.yaml

Window functions:
- Ranking: rank, dense_rank, row_number, percent_rank, cume_dist
- Offset: ntile, lead, lag, shift
- Value: first_value, last_value, nth_value, first, last
- Cumulative: cum_sum, cum_max, cum_min, cum_count, cum_prod
- Fill: forward_fill, backward_fill
- Difference: diff
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class SubstraitWindowArithmeticAPIBuilderProtocol(Protocol):
    """Builder protocol for window arithmetic operations.

    Defines user-facing fluent API methods that create window function nodes.
    """

    def rank(
        self,
        method: Literal["average", "min", "max", "dense", "ordinal"] = "average",
        *,
        descending: bool = False,
    ) -> BaseExpressionAPI:
        """Rank values within a partition."""
        ...

    def dense_rank(self, *, descending: bool = False) -> BaseExpressionAPI:
        """Dense rank (no gaps) within a partition."""
        ...

    def row_number(self, *, descending: bool = False) -> BaseExpressionAPI:
        """Row number (unique sequential) within a partition."""
        ...

    def percent_rank(self) -> BaseExpressionAPI:
        """Relative rank within the partition (0..1)."""
        ...

    def cume_dist(self) -> BaseExpressionAPI:
        """Cumulative distribution within the partition (0..1)."""
        ...

    def ntile(self, n: int) -> BaseExpressionAPI:
        """Divide partition into n buckets and return bucket number."""
        ...

    def lead(
        self,
        offset: Union[BaseExpressionAPI, int] = 1,
        default: Optional[Union[BaseExpressionAPI, Any]] = None,
    ) -> BaseExpressionAPI:
        """Value at offset rows after current row."""
        ...

    def lag(
        self,
        offset: Union[BaseExpressionAPI, int] = 1,
        default: Optional[Union[BaseExpressionAPI, Any]] = None,
    ) -> BaseExpressionAPI:
        """Value at offset rows before current row."""
        ...

    def first_value(self) -> BaseExpressionAPI:
        """First value in the window frame."""
        ...

    def last_value(self) -> BaseExpressionAPI:
        """Last value in the window frame."""
        ...

    def nth_value(self, n: Union[BaseExpressionAPI, int] = 1) -> BaseExpressionAPI:
        """Nth value in the window frame (1-based)."""
        ...

    def cum_sum(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative sum."""
        ...

    def cum_max(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative maximum."""
        ...

    def cum_min(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative minimum."""
        ...

    def cum_count(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative count."""
        ...

    def cum_prod(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative product."""
        ...

    def shift(
        self,
        n: Union[BaseExpressionAPI, int] = 1,
        *,
        fill_value: Optional[Union[BaseExpressionAPI, Any]] = None,
    ) -> BaseExpressionAPI:
        """Shift values by n positions."""
        ...

    def first(self) -> BaseExpressionAPI:
        """First value in the window frame (alias for first_value)."""
        ...

    def last(self) -> BaseExpressionAPI:
        """Last value in the window frame (alias for last_value)."""
        ...

    def forward_fill(self, limit: Optional[int] = None) -> BaseExpressionAPI:
        """Forward fill null values."""
        ...

    def backward_fill(self, limit: Optional[int] = None) -> BaseExpressionAPI:
        """Backward fill null values."""
        ...

    def diff(self, n: int = 1) -> BaseExpressionAPI:
        """Consecutive difference: value[i] - value[i-n]."""
        ...
