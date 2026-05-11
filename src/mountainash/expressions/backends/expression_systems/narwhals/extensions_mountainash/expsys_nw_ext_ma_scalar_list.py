"""Narwhals backend for mountainash list operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarListExpressionSystemProtocol


class MountainAshNarwhalsScalarListExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarListExpressionSystemProtocol[nw.Expr]):
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

    def list_median(self, x, /):
        return x.list.median()

    def list_all(self, x, /):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.all(). Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ALL,
        )

    def list_any(self, x, /):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.any(). Use Polars or Ibis backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ANY,
        )

    def list_drop_nulls(self, x, /):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.drop_nulls(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.DROP_NULLS,
        )

    def list_std(self, x, /, *, ddof: int = 1):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.std(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.STD,
        )

    def list_var(self, x, /, *, ddof: int = 1):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.var(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.VAR,
        )

    def list_n_unique(self, x, /):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.n_unique(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.N_UNIQUE,
        )

    def list_count_matches(self, x, /, item):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.count_matches(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.COUNT_MATCHES,
        )

    def list_item(self, x, /, *, index: int = 0):
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
        raise BackendCapabilityError(
            "Narwhals does not support list.item(). Use Polars backend.",
            backend=self.BACKEND_NAME,
            function_key=FKEY_MOUNTAINASH_SCALAR_LIST.ITEM,
        )
