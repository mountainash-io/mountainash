"""Polars backend for mountainash extension window operations."""

from __future__ import annotations

import polars as pl
from polars import Expr as PolarsExpr

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem


class MountainAshPolarsWindowExpressionSystem(PolarsBaseExpressionSystem):
    """Polars implementation of mountainash window extensions."""

    def diff(self, x: PolarsExpr, /, *, n: int = 1) -> PolarsExpr:
        """Consecutive difference: value[i] - value[i-n]."""
        return x.diff(n=n)
