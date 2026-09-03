"""Import-safe Ibis relation-backend capability declarations.

Migrated from ``mountainash.relations.backends.relation_systems.ibis_relation_capabilities``
(2026-08 capability-architecture PR). Extracted; the source module still
self-registers until Task 11 rewires the base classes.
"""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
)
from mountainash.core.capabilities.schema import Clause, ClauseOp, Predicate
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.relation_systems.resource_files import (
    IBIS_NON_DEFAULT_DIALECT_CONDITION,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)

IBIS_REL_CAPABILITIES: tuple[CapabilityFact, ...] = (
    CapabilityFact(
        operation_key=RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX,
        param="*",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-polars",
        message="with_row_index lowers to a window function (row_number); the ibis Polars "
                "backend has no WindowFunction translation rule.",
        workaround="Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.",
        upstream_ref="IB-REL-01",
        since="2026-08-01",
        probe_exempt="relation op-level gap; covered by relation with_row_index cross-backend tests",
    ),
    CapabilityFact(
        operation_key=RKEY_MOUNTAINASH_REL.READ_RESOURCE, param="resource",
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.IBIS,
        message="CSV dialect fields require the portable provider fallback reader",
        workaround="none needed — mountainash routes automatically",
        since="2026-08-30",
        condition=IBIS_NON_DEFAULT_DIALECT_CONDITION,
        enforcement=Enforcement.ROUTER_METADATA,
        probe_exempt="router, not gate — fallback handles it; behaviour covered by relations resource tests",
    ),
    CapabilityFact(
        operation_key=RKEY_MOUNTAINASH_REL.JOIN_ASOF,
        param="strategy",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect="ibis-polars",
        message="join_asof forward/nearest lowers to a non-equality candidate join; the "
                "ibis Polars backend rejects non-equality join predicates "
                "(TypeError: Only equality join predicates supported with pandas).",
        workaround="Use ibis-duckdb/ibis-sqlite, or polars/narwhals backends.",
        upstream_ref="IB-REL-15",
        since="2026-08-18",
        predicate=Predicate(clauses=(
            Clause(path="strategy", op=ClauseOp.IN,
                   operand=frozenset({"forward", "nearest"})),
        )),
    ),
)


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)


_EVIDENCE = ProbeEvidence(
    probe_date="2026-07-05",  # earliest `since` in the tuple (2026-07-05 vs 2026-08-01)
    library_versions=(),      # not recorded in the source declarations
    fixtures=(),
)


DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS, domain=Domain.RELATION,
        source=FactSource.MOUNTAINASH, facts=IBIS_REL_CAPABILITIES,
        evidence=_EVIDENCE,
    ),
)
