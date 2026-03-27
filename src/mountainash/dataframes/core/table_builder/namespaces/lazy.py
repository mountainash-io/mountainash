"""
LazyNamespace - Lazy/eager execution operations.

Provides:
    - collect() - Collect lazy DataFrame to eager
    - lazy() - Convert eager DataFrame to lazy
    - execute() - Alias for collect
    - materialize() - Alias for collect
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..base import BaseTableBuilder

from ..base import BaseNamespace
from ...protocols import LazyBuilderProtocol


class LazyNamespace(BaseNamespace, LazyBuilderProtocol):
    """
    Namespace for lazy/eager execution operations.

    These operations control when computation actually happens.
    """

    def collect(self) -> "BaseTableBuilder":
        """
        Collect lazy DataFrame to eager.

        For lazy DataFrames (Polars LazyFrame, Ibis Table), this
        executes all pending operations and returns an eager DataFrame.
        For already-eager DataFrames, returns as-is.

        Returns:
            New TableBuilder with collected (eager) DataFrame

        Example:
            result = table(lazy_df).filter(...).select(...).collect()
        """
        result = self._system.collect(self._df)
        return self._build(result)

    def lazy(self) -> "BaseTableBuilder":
        """
        Convert eager DataFrame to lazy.

        For backends that support lazy evaluation (Polars), converts
        the DataFrame to lazy mode for deferred execution.
        For backends without lazy support, returns as-is.

        Returns:
            New TableBuilder with lazy DataFrame

        Example:
            lazy_result = table(df).lazy().filter(...).select(...)
        """
        result = self._system.lazy(self._df)
        return self._build(result)

    def execute(self) -> "BaseTableBuilder":
        """
        Execute and collect results.

        Alias for collect() (SQL-style naming).

        Returns:
            New TableBuilder with executed results

        Example:
            result = table(ibis_table).filter(...).execute()
        """
        return self.collect()

    def materialize(self) -> "BaseTableBuilder":
        """
        Materialize lazy computation.

        Alias for collect().

        Returns:
            New TableBuilder with materialized DataFrame

        Example:
            result = table(lazy_df).filter(...).materialize()
        """
        return self.collect()

    def cache(self) -> "BaseTableBuilder":
        """
        Cache the current state.

        For lazy DataFrames, this collects and re-wraps the result,
        effectively caching intermediate computations.

        Returns:
            New TableBuilder with cached DataFrame

        Example:
            cached = table(df).filter(...).cache()
            # Use cached for multiple downstream operations
            result1 = cached.select("a", "b")
            result2 = cached.select("c", "d")
        """
        # Collect to eager, then optionally convert back to lazy
        collected = self._system.collect(self._df)
        return self._build(collected)

    def persist(self) -> "BaseTableBuilder":
        """
        Alias for cache().

        Returns:
            New TableBuilder with persisted DataFrame

        Example:
            persisted = table(df).persist()
        """
        return self.cache()
