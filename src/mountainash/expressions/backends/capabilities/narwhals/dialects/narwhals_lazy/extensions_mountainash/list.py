"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.LIST,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="item_type",
                selector=Selector(kind="exact", value="datetime"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="item_type",
                selector=Selector(kind="exact", value="time"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="item_type", op=ClauseOp.EQ, operand="integer"),
                        )
                    ),
                ),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="item_type", op=ClauseOp.EQ, operand="boolean"),
                        )
                    ),
                ),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="item_type", op=ClauseOp.EQ, operand="number"),
                        )
                    ),
                ),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.PARSE,
                subject="failure_behavior",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="item_type", op=ClauseOp.EQ, operand="date"),
                        )
                    ),
                ),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="This backend cannot execute LIST.PARSE for the requested item type and failure behavior",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_LIST.CAST_ITEMS,
                subject="failure_behavior",
                selector=Selector(kind="exact", value="null"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="Native Narwhals list item casts do not implement null-on-invalid behavior.",
        ),
    ),
)
