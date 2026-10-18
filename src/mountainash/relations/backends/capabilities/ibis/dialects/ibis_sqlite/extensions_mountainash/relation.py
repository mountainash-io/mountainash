"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilitySegment

from mountainash.core.capabilities.declarations import Domain
from mountainash.relations.backends.capabilities.ibis.family.extensions_mountainash.relation import SEEDED_COUNT_POLICY


SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    policies=(SEEDED_COUNT_POLICY,),
    changes=(),
)
