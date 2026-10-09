"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import Domain


# Exact numeric target refusals are intrinsic backend checks, not optional policies.
SEGMENT = CapabilitySegment(domain=Domain.VALUE, changes=())
