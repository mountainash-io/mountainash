"""Ibis backend for mountainash extension window operations."""

from __future__ import annotations

from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainashWindowExpressionSystemProtocol


class MountainAshIbisWindowExpressionSystem(IbisBaseExpressionSystem, MountainashWindowExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of mountainash window extensions."""

    def diff(self, x, /, *, n: int = 1):
        """Consecutive difference: value[i] - value[i-n]."""
        return x - x.lag(offset=n)

    def cum_sum(self, x, /, *, reverse: bool = False):
        """Cumulative sum — returns reduction; apply_window adds frame bounds."""
        return x.sum()

    def cum_max(self, x, /, *, reverse: bool = False):
        """Cumulative maximum — returns reduction; apply_window adds frame bounds."""
        return x.max()

    def cum_min(self, x, /, *, reverse: bool = False):
        """Cumulative minimum — returns reduction; apply_window adds frame bounds."""
        return x.min()

    def cum_count(self, x, /, *, reverse: bool = False):
        """Cumulative count — returns reduction; apply_window adds frame bounds."""
        return x.count()

    def cum_prod(self, x, /, *, reverse: bool = False):
        """Cumulative product — returns reduction; apply_window adds frame bounds."""
        return x.prod()

    def forward_fill(self, x, /, *, limit: int | None = None):
        """Forward fill null values."""
        return x.fill_null(method="ffill")

    def backward_fill(self, x, /, *, limit: int | None = None):
        """Backward fill null values."""
        return x.fill_null(method="bfill")
