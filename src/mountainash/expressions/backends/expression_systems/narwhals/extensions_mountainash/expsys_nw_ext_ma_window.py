"""Narwhals backend for mountainash extension window operations."""

from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainashWindowExpressionSystemProtocol


class MountainAshNarwhalsWindowExpressionSystem(NarwhalsBaseExpressionSystem, MountainashWindowExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of mountainash window extensions."""

    def diff(self, x, /, *, n: int = 1):
        """Consecutive difference: value[i] - value[i-n]."""
        if n != 1:
            raise NotImplementedError(
                "Narwhals diff() only supports n=1. "
                "Use Polars or Ibis backend for n > 1."
            )
        return x.diff()

    def cum_sum(self, x, /, *, reverse: bool = False):
        """Cumulative sum."""
        return x.cum_sum(reverse=reverse)

    def cum_max(self, x, /, *, reverse: bool = False):
        """Cumulative maximum."""
        return x.cum_max(reverse=reverse)

    def cum_min(self, x, /, *, reverse: bool = False):
        """Cumulative minimum."""
        return x.cum_min(reverse=reverse)

    def cum_count(self, x, /, *, reverse: bool = False):
        """Cumulative count."""
        return x.cum_count(reverse=reverse)

    def cum_prod(self, x, /, *, reverse: bool = False):
        """Cumulative product."""
        return x.cum_prod(reverse=reverse)

    def forward_fill(self, x, /, *, limit: int | None = None):
        """Forward fill null values."""
        if limit is not None:
            return x.forward_fill(limit=limit)
        return x.forward_fill()

    def backward_fill(self, x, /, *, limit: int | None = None):
        """Backward fill null values."""
        if limit is not None:
            return x.backward_fill(limit=limit)
        return x.backward_fill()
