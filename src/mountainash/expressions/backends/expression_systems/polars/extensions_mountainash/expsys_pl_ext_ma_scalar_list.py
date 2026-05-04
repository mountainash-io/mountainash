"""Polars backend for mountainash list operations."""
from __future__ import annotations

import polars as pl

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarListExpressionSystemProtocol


class MountainAshPolarsScalarListExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarListExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of list operations."""

    def list_sum(self, x, /):
        return x.list.sum()

    def list_min(self, x, /):
        return x.list.min()

    def list_max(self, x, /):
        return x.list.max()

    def list_mean(self, x, /):
        return x.list.mean()

    def list_len(self, x, /):
        return x.list.len()

    def list_contains(self, x, /, item):
        return x.list.contains(item)

    def list_sort(self, x, /, *, descending: bool = False):
        return x.list.sort(descending=descending)

    def list_unique(self, x, /):
        return x.list.unique()

    def list_explode(self, x, /):
        return x.list.explode()

    def list_join(self, x, /, *, separator: str = ","):
        return x.list.join(separator)

    def list_get(self, x, /, *, index: int = 0):
        return x.list.get(index, null_on_oob=True)
