"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilitySegment

from mountainash.core.capabilities.declarations import Domain


SEGMENT = CapabilitySegment(
    domain=Domain.WINDOW,
    changes=(),
)
