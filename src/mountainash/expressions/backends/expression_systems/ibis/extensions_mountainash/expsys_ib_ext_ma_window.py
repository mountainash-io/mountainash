"""Ibis backend for mountainash extension window operations."""

from __future__ import annotations

from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem


class MountainAshIbisWindowExpressionSystem(IbisBaseExpressionSystem):
    """Ibis implementation of mountainash window extensions."""

    def diff(self, x, /, *, n: int = 1):
        """Consecutive difference: value[i] - value[i-n]."""
        return x - x.lag(offset=n)

    def cum_sum(self, x, /, *, reverse: bool = False):
        """Cumulative sum."""
        import ibis
        if reverse:
            return x.sum().over(ibis.window(rows=(0, None)))
        return x.cumsum()

    def cum_max(self, x, /, *, reverse: bool = False):
        """Cumulative maximum."""
        import ibis
        if reverse:
            return x.max().over(ibis.window(rows=(0, None)))
        return x.cummax()

    def cum_min(self, x, /, *, reverse: bool = False):
        """Cumulative minimum."""
        import ibis
        if reverse:
            return x.min().over(ibis.window(rows=(0, None)))
        return x.cummin()

    def cum_count(self, x, /, *, reverse: bool = False):
        """Cumulative count."""
        import ibis
        if reverse:
            return x.count().over(ibis.window(rows=(0, None)))
        return x.count().over(ibis.cumulative_window())
