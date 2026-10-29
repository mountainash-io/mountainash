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
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_CATEGORICAL

SEGMENT = CapabilitySegment(
    domain=Domain.CATEGORICAL,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_CATEGORICAL.CAST,
                subject="value_type",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="value_type", op=ClauseOp.EQ, operand="integer"),
                        )
                    ),
                ),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="This backend cannot execute CATEGORICAL.CAST for the requested value type and failure behavior",
            applicability=unbounded,
        ),
    ),
)
