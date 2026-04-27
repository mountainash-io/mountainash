"""Ibis backend for mountainash extension window operations."""

from __future__ import annotations

from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem


class MountainAshIbisWindowExpressionSystem(IbisBaseExpressionSystem):
    """Ibis implementation of mountainash window extensions."""

    def diff(self, x, /, *, n: int = 1):
        """Consecutive difference: value[i] - value[i-n]."""
        return x - x.lag(offset=n)
