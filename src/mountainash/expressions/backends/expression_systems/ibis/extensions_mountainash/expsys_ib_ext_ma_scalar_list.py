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
