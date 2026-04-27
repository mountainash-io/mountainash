"""Protocol for mountainash extension window operations.

Mountainash Extension: Window Operations
URI: None (mountainash-specific, not Substrait)

Extensions beyond Substrait standard:
- diff: Consecutive row difference
- cum_sum: Cumulative sum
- cum_max: Cumulative maximum
- cum_min: Cumulative minimum
- cum_count: Cumulative count
"""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class MountainashWindowExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for mountainash extension window operations.

    These operations extend Substrait's window capabilities with
    cumulative and diff operations common in DataFrame libraries.
    """

    def diff(self, x: ExpressionT, /, *, n: int = 1) -> ExpressionT:
        """Consecutive difference: value[i] - value[i-n]. First n elements are null."""
        ...

    def cum_sum(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
        """Cumulative sum."""
        ...

    def cum_max(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
        """Cumulative maximum."""
        ...

    def cum_min(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
        """Cumulative minimum."""
        ...

    def cum_count(self, x: ExpressionT, /, *, reverse: bool = False) -> ExpressionT:
        """Cumulative count."""
        ...
