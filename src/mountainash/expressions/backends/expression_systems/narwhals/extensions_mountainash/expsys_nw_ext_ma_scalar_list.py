"""Narwhals backend for mountainash list operations."""
from __future__ import annotations

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem


class MountainAshNarwhalsScalarListExpressionSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of list operations."""

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
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.explode(). "
            "Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.EXPLODE,
        )

    def list_join(self, x, /, *, separator: str = ","):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.join(). "
            "Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.JOIN,
        )

    def list_get(self, x, /, *, index: int = 0):
        return x.list.get(index)
