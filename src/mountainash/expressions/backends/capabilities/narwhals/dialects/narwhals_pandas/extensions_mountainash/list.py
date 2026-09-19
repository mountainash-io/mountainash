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
from mountainash.core.capabilities.declarations import CapabilityPolicyRule, QualifiedInformationKey
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND

_SCOPE = Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-pandas"))

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
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS, subject="item"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals list.contains() requires a literal item argument, not a column expression",
            workaround="Use a literal value for item or use the Polars/Ibis backend.",
            issue="NW-LIST-01",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS, subject="item"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-07-05",
            message="Narwhals list.t_contains() requires a literal item argument, not a column expression",
            workaround="Use a literal value for item or use the Polars/Ibis backend.",
            issue="NW-LIST-01",
        ),
        *(
            CapabilityInformation(
                key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.PARSE, "*"),
                layer=InformationLayer.NATIVE,
                level=CapabilityLevel.UNSUPPORTED,
                since="2026-08-24",
                message="Native Narwhals string splitting used by list parsing requires Arrow-backed pandas string storage.",
                workaround="Use Arrow-backed pandas strings, Polars, or Ibis.",
            ),
            CapabilityInformation(
                key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS, "*"),
                layer=InformationLayer.NATIVE,
                level=CapabilityLevel.UNSUPPORTED,
                since="2026-07-05",
                message="The pandas list namespace rejects non-Arrow list storage; contains remains independently unimplemented on Arrow lists in the observed Narwhals version.",
                workaround="Use Polars or Ibis list membership; Arrow conversion alone does not implement contains.",
                issue="NW-LIST-01",
            ),
            CapabilityInformation(
                key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS, "*"),
                layer=InformationLayer.NATIVE,
                level=CapabilityLevel.UNSUPPORTED,
                since="2026-07-05",
                message="The native contains operation used by ternary membership requires Arrow list storage and remains independently unimplemented on pandas Arrow lists.",
                workaround="Use Polars or Ibis for ternary list membership.",
                issue="NW-LIST-01",
            ),
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.PARSE, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-24",
            message="Narwhals list parsing requires Arrow-backed pandas string storage.",
            consumer=PolicyConsumer.MATERIALIZATION_ERROR,
            action=PolicyAction.ENRICH,
            native_errors=(TypeError,),
            native_issue="narwhals:arrow-string-storage",
            information=QualifiedInformationKey(
                _SCOPE, CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.PARSE, "*"), InformationLayer.NATIVE
            ),
        ),
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-05",
            message="Narwhals pandas list membership requires Arrow-backed list storage.",
            consumer=PolicyConsumer.MATERIALIZATION_ERROR,
            action=PolicyAction.ENRICH,
            native_errors=(TypeError,),
            native_issue="narwhals:arrow-list-storage",
            information=QualifiedInformationKey(
                _SCOPE, CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS, "*"), InformationLayer.NATIVE
            ),
        ),
        CapabilityPolicyRule(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS, "*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-05",
            message="Narwhals pandas ternary list membership requires Arrow-backed list storage.",
            consumer=PolicyConsumer.MATERIALIZATION_ERROR,
            action=PolicyAction.ENRICH,
            native_errors=(TypeError,),
            native_issue="narwhals:arrow-list-storage",
            information=QualifiedInformationKey(
                _SCOPE, CapabilityKey(FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS, "*"), InformationLayer.NATIVE
            ),
        ),
    ),
)
