"""Polars implementation of Substrait ReadRel."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.types import is_polars_lazyframe, is_polars_dataframe
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitReadRelationSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.core.types import PolarsLazyFrame


class SubstraitPolarsReadRelationSystem(SubstraitReadRelationSystemProtocol):
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
