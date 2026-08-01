"""Import-safe Ibis relation capability declarations."""

from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
)
from mountainash.core.constants import CONST_BACKEND
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
        message="CSV dialect field 'escape_char' is not native-safe on this backend's "
                "reader — routed to the CsvSpec fallback reader",
        workaround="none needed — mountainash routes automatically",
        since="2026-07-05",
        condition="resource.dialect.escape_char is set",
        enforcement=Enforcement.ROUTER_METADATA,
        probe_exempt="router, not gate — fallback handles it; behaviour covered by relations resource tests",
    ),
)


CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, IBIS_REL_CAPABILITIES)
