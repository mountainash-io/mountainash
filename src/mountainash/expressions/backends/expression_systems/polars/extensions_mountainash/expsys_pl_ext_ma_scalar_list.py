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

    def list_all(self, x, /):
        return x.list.all()

    def list_any(self, x, /):
        return x.list.any()

    def list_drop_nulls(self, x, /):
        return x.list.drop_nulls()

    def list_median(self, x, /):
        return x.list.median()

    def list_std(self, x, /, *, ddof: int = 1):
        return x.list.std(ddof=ddof)

    def list_var(self, x, /, *, ddof: int = 1):
        return x.list.var(ddof=ddof)

    def list_n_unique(self, x, /):
        return x.list.n_unique()

    def list_count_matches(self, x, /, item):
        return x.list.count_matches(item)

    def list_item(self, x, /, *, index: int = 0):
        return x.list.get(index, null_on_oob=True)

    def list_reverse(self, x, /):
        return x.list.reverse()

    def list_head(self, x, /, n):
        return x.list.head(n)

    def list_tail(self, x, /, n):
        return x.list.tail(n)

    def list_slice(self, x, /, offset, *, length=None):
        return x.list.slice(offset, length)

    def list_gather(self, x, /, indices, *, null_on_oob=False):
        return x.list.gather(indices, null_on_oob=null_on_oob)

    def list_gather_every(self, x, /, n, *, offset=0):
        return x.list.gather_every(n, offset=offset)

    def list_shift(self, x, /, n):
        return x.list.shift(n)

    def list_diff(self, x, /, *, n=1, null_behavior="ignore"):
        return x.list.diff(n=n, null_behavior=null_behavior)

    def list_set_union(self, x, /, other):
        return x.list.set_union(other)

    def list_set_intersection(self, x, /, other):
        return x.list.set_intersection(other)

    def list_set_difference(self, x, /, other):
        return x.list.set_difference(other)

    def list_set_symmetric_difference(self, x, /, other):
        return x.list.set_symmetric_difference(other)

    def list_concat(self, x, /, other):
        return x.list.concat(other)

    def list_filter(self, x, /, mask):
        return x.list.filter(mask)
