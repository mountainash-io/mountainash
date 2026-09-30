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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_BOOLEAN

SEGMENT = CapabilitySegment(
    domain=Domain.BOOLEAN,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_BOOLEAN.PARSE_TOKENS,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(clauses=(Clause(path="failure_behavior", op=ClauseOp.EQ, operand="throw"),)),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            message="ibis-sqlite cannot enforce throw-on-invalid boolean tokens",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
    ),
)
