"""Narwhals implementation of Substrait FetchRel."""

from __future__ import annotations

from typing import Any, Optional

import narwhals as nw

from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitFetchRelationSystemProtocol,
)


class SubstraitNarwhalsFetchRelationSystem(
    SubstraitFetchRelationSystemProtocol[nw.DataFrame | nw.LazyFrame]
):
    """Offset/limit row retrieval on Narwhals DataFrames."""

    def fetch(self, relation: Any, offset: int, count: Optional[int], /) -> Any:
        is_lazy = isinstance(relation, nw.LazyFrame)
        if not is_lazy:
            sliced = relation.gather_every(n=1, offset=offset) if offset else relation
            return sliced if count is None else sliced.head(count)
        implementation = relation.implementation
        native = relation.to_native()
        if implementation is nw.Implementation.DASK and offset == 0:
            if count is None:
                return relation
            return relation.head(count)
        from mountainash.relations.backends.relation_systems.narwhals.extensions_mountainash.relsys_nw_ext_ma_util import (
            _as_duckdb, _spark_position,
        )

        duckdb_relation = _as_duckdb(relation)
        if duckdb_relation is not None:
            limit = min(count, 2**63 - 1) if count is not None else 2**63 - 1
            return nw.from_native(duckdb_relation.limit(limit, offset=min(offset, 2**63 - 1)))
        if offset == 0 and count is None:
            return relation
        if implementation in {
            nw.Implementation.PYSPARK, nw.Implementation.PYSPARK_CONNECT, nw.Implementation.SQLFRAME,
        }:
            if offset == 0 and count is not None and count <= 2**31 - 1:
                return nw.from_native(native.limit(count))
            return nw.from_native(_spark_position(relation, offset=offset, count=count))
        sliced = relation.gather_every(n=1, offset=offset) if offset else relation
        return sliced if count is None else sliced.head(count)
