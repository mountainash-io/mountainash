"""Polars implementation of Substrait ReadRel."""

from __future__ import annotations

from typing import Any

from mountainash.core.types import (
    PolarsLazyFrame, is_polars_lazyframe, is_polars_dataframe,
)


class SubstraitPolarsReadRelationSystem:
    """Read / scan a data source into a Polars LazyFrame."""

    def read(self, dataframe: Any, /) -> PolarsLazyFrame:
        if is_polars_lazyframe(dataframe):
            return dataframe
        if is_polars_dataframe(dataframe):
            return dataframe.lazy()
        raise TypeError(
            f"Polars backend cannot read {type(dataframe).__name__}. "
            f"Expected polars.DataFrame or polars.LazyFrame."
        )
