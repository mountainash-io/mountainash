"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilitySegment, Domain

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
)
