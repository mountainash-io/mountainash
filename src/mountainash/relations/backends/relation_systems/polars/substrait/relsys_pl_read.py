"""Polars implementation of Substrait ReadRel."""

from __future__ import annotations

from typing import Any

import polars as pl


class SubstraitPolarsReadRelationSystem:
    """Read / scan a data source into a Polars LazyFrame."""

    def read(self, dataframe: Any, /) -> pl.LazyFrame:
        if isinstance(dataframe, pl.LazyFrame):
            return dataframe
        if isinstance(dataframe, pl.DataFrame):
            return dataframe.lazy()
        raise TypeError(
            f"Polars backend cannot read {type(dataframe).__name__}. "
            f"Expected polars.DataFrame or polars.LazyFrame."
        )
