"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.schema import Enforcement
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.UNNEST, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-05",
            message="unnest() is not supported by the Narwhals backend",
            workaround="Use the Polars backend for unnest.",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF, subject="tolerance"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-05",
            message="join_asof(tolerance=...) is not supported by the Narwhals backend",
            workaround="Drop tolerance= or use the Polars backend.",
            condition="tolerance is not None",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.READ_RESOURCE, subject="resource"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-30",
            message="CSV dialect fields require the portable provider fallback reader",
            workaround="none needed — mountainash routes automatically",
            condition="resource.dialect.comment_char is set or resource.dialect.comment_rows is set or resource.dialect.double_quote is set or resource.dialect.escape_char is set or resource.dialect.header_join is set or resource.dialect.header_rows is set or resource.dialect.line_terminator is set or resource.dialect.skip_initial_space is set",
            probe_exempt="router, not gate — fallback handles it; behaviour covered by relations resource tests",
            enforcement=Enforcement.ROUTER_METADATA,
        ),
    ),
)
