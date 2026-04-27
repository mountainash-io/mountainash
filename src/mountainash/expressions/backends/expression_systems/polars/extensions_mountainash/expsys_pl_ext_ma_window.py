"""Polars backend for mountainash extension window operations."""

from __future__ import annotations

from polars import Expr as PolarsExpr

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem


class MountainAshPolarsWindowExpressionSystem(PolarsBaseExpressionSystem):
    """Polars implementation of mountainash window extensions."""

    def diff(self, x: PolarsExpr, /, *, n: int = 1) -> PolarsExpr:
        """Consecutive difference: value[i] - value[i-n]."""
        return x.diff(n=n)

    def cum_sum(self, x: PolarsExpr, /, *, reverse: bool = False) -> PolarsExpr:
        """Cumulative sum."""
        return x.cum_sum(reverse=reverse)

    def cum_max(self, x: PolarsExpr, /, *, reverse: bool = False) -> PolarsExpr:
        """Cumulative maximum."""
        return x.cum_max(reverse=reverse)

    def cum_min(self, x: PolarsExpr, /, *, reverse: bool = False) -> PolarsExpr:
        """Cumulative minimum."""
        return x.cum_min(reverse=reverse)

    def cum_count(self, x: PolarsExpr, /, *, reverse: bool = False) -> PolarsExpr:
        """Cumulative count."""
        return x.cum_count(reverse=reverse)
