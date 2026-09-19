"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import Domain
from mountainash.core.capabilities.schema import CapabilityLevel
from mountainash.core.capabilities.schema import InformationLayer
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL


SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.READ_RESOURCE, subject="resource"),
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-30",
            message="CSV dialect features use the portable provider fallback reader rather than Polars resource ingestion.",
            workaround="none needed — mountainash routes automatically",
        ),
    ),
)
