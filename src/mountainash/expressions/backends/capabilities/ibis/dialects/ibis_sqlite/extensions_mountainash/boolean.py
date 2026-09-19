"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_BOOLEAN
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

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
            since="2026-08-25",
            message="ibis-sqlite cannot enforce throw-on-invalid boolean tokens",
            layer=InformationLayer.NATIVE,
        ),
    ),
)
