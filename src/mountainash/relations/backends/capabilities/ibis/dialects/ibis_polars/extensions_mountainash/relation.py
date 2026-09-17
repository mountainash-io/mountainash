"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-01",
            message="with_row_index lowers to a window function (row_number); the ibis Polars backend has no WindowFunction translation rule.",
            workaround="Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.",
            issue="IB-REL-01",
            probe_exempt="relation op-level gap; covered by relation with_row_index cross-backend tests",
        ),
        CapabilityAssertion(
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
            since="2026-08-18",
            message="join_asof forward/nearest lowers to a non-equality candidate join; the ibis Polars backend rejects non-equality join predicates (TypeError: Only equality join predicates supported with pandas).",
            workaround="Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.",
            issue="IB-REL-15",
        ),
    ),
)
