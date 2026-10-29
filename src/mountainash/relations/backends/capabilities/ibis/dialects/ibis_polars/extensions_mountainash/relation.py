"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilitySegment,
    Domain,
    Selector,
)
from mountainash.core.capabilities.schema import CapabilityLevel, Clause, ClauseOp, InformationLayer, Predicate
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            message="with_row_index lowers to a window function (row_number); the ibis Polars backend has no WindowFunction translation rule.",
            workaround="Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.",
            issue="IB-REL-01",
            layer=InformationLayer.PUBLIC,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF,
                subject="strategy",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(
                                path="strategy",
                                op=ClauseOp.IN,
                                operand=frozenset(
                                    (
                                        "forward",
                                        "nearest",
                                    )
                                ),
                            ),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            message="join_asof forward/nearest lowers to a non-equality candidate join; the ibis Polars backend rejects non-equality join predicates (TypeError: Only equality join predicates supported with pandas).",
            workaround="Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.",
            issue="IB-REL-15",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
    ),
)
