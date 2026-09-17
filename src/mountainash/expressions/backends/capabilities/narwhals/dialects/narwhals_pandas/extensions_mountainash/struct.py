"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.STRUCT,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(clauses=(Clause(path="failure_behavior", op=ClauseOp.EQ, operand="throw"),)),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute STRUCT.CAST for the requested failure behavior",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(clauses=(Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),)),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute STRUCT.CAST for the requested failure behavior",
        ),
    ),
)
