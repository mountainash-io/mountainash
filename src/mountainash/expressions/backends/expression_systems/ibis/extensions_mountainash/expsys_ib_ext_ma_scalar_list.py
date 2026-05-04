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
