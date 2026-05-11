"""Ibis backend for mountainash list operations."""
from __future__ import annotations

from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.ibis.base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarListExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST


class MountainAshIbisScalarListExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarListExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of list operations."""

    def list_sum(self, x, /):
        return x.sums()

    def list_min(self, x, /):
        return x.mins()

    def list_max(self, x, /):
        return x.maxs()

    def list_mean(self, x, /):
        return x.means()

    def list_len(self, x, /):
        return x.length()

    def list_contains(self, x, /, item):
        return x.contains(item)

    def list_sort(self, x, /, *, descending: bool = False):
        if descending:
            raise BackendCapabilityError(
                "Ibis ArrayValue.sort() does not support descending order. "
                "Use ascending sort, or use Polars/Narwhals backend for descending list sort.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SORT,
            )
        return x.sort()

    def list_unique(self, x, /):
        return x.unique()

    def list_explode(self, x, /):
        return x.unnest()

    def list_join(self, x, /, *, separator: str = ","):
        return x.join(separator)

    def list_get(self, x, /, *, index: int = 0):
        return x[index]

    def list_all(self, x, /):
        return x.alls()

    def list_any(self, x, /):
        return x.anys()

    def list_drop_nulls(self, x, /):
        raise BackendCapabilityError(
            "Ibis does not support array.drop_nulls(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS,
        )

    def list_median(self, x, /):
        raise BackendCapabilityError(
            "Ibis does not support array.median(). Use Polars or Narwhals backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.MEDIAN,
        )

    def list_std(self, x, /, *, ddof: int = 1):
        raise BackendCapabilityError(
            "Ibis does not support array.std(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.STD,
        )

    def list_var(self, x, /, *, ddof: int = 1):
        raise BackendCapabilityError(
            "Ibis does not support array.var(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.VAR,
        )

    def list_n_unique(self, x, /):
        raise BackendCapabilityError(
            "Ibis does not support array.n_unique(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE,
        )

    def list_count_matches(self, x, /, item):
        raise BackendCapabilityError(
            "Ibis does not support array.count_matches(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES,
        )

    def list_item(self, x, /, *, index: int = 0):
        raise BackendCapabilityError(
            "Ibis does not support array.item(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ITEM,
        )

    def list_reverse(self, x, /):
        raise BackendCapabilityError(
            "Ibis does not support array.reverse(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.REVERSE,
        )

    def list_head(self, x, /, n):
        raise BackendCapabilityError(
            "Ibis does not support array.head(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.HEAD,
        )

    def list_tail(self, x, /, n):
        raise BackendCapabilityError(
            "Ibis does not support array.tail(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.TAIL,
        )

    def list_slice(self, x, /, offset, *, length=None):
        raise BackendCapabilityError(
            "Ibis does not support array.slice(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SLICE,
        )

    def list_gather(self, x, /, indices, *, null_on_oob=False):
        raise BackendCapabilityError(
            "Ibis does not support array.gather(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GATHER,
        )

    def list_gather_every(self, x, /, n, *, offset=0):
        raise BackendCapabilityError(
            "Ibis does not support array.gather_every(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.GATHER_EVERY,
        )

    def list_shift(self, x, /, n):
        raise BackendCapabilityError(
            "Ibis does not support array.shift(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SHIFT,
        )

    def list_diff(self, x, /, *, n=1, null_behavior="ignore"):
        raise BackendCapabilityError(
            "Ibis does not support array.diff(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.DIFF,
        )

    def list_set_union(self, x, /, other):
        return x.union(other)

    def list_set_intersection(self, x, /, other):
        return x.intersect(other)

    def list_set_difference(self, x, /, other):
        raise BackendCapabilityError(
            "Ibis does not support array.set_difference(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_DIFFERENCE,
        )

    def list_set_symmetric_difference(self, x, /, other):
        raise BackendCapabilityError(
            "Ibis does not support array.set_symmetric_difference(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.SET_SYMMETRIC_DIFFERENCE,
        )

    def list_concat(self, x, /, other):
        return x.concat(other)

    def list_filter(self, x, /, mask):
        raise BackendCapabilityError(
            "Ibis array.filter() requires a Deferred/Callable predicate, "
            "which is incompatible with mountainash's compiled expression model. "
            "Use Polars backend for list.filter().",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.FILTER,
        )
