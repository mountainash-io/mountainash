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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT

SEGMENT = CapabilitySegment(
    domain=Domain.STRUCT,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(clauses=(Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),)),
                ),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="This backend cannot execute STRUCT.CAST for the requested failure behavior",
            applicability=unbounded,
        ),
    ),
)
