"""Window-shape refusals for this Narwhals dialect."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    QualifiedInformationKey,
    Selector,
)
from mountainash.core.capabilities.predicates import WINDOW_ROOT
from mountainash.core.capabilities.schema import (
    CapabilityIssueClass,
    CapabilityLevel,
    Clause,
    ClauseOp,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
    Predicate,
)
from mountainash.expressions.backends.capabilities.narwhals.family._scope import SCOPE as FAMILY_SCOPE
from mountainash.expressions.core.expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW

_DESCENDING_MESSAGE = "Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported."
_DESCENDING_KEYS = tuple(
    CapabilityKey(
        operation=operation,
        subject=WINDOW_ROOT,
        selector=Selector(kind="predicate", value=Predicate(clauses=(
            Clause(path=f"{WINDOW_ROOT}.any_descending", op=ClauseOp.EQ, operand=True),
        ))),
    )
    for operation in (
        SUBSTRAIT_ARITHMETIC_WINDOW.LAG,
        SUBSTRAIT_ARITHMETIC_WINDOW.LEAD,
        SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE,
        SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE,
        SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE,
    )
)

SEGMENT = CapabilitySegment(
    domain=Domain.WINDOW,
    changes=(),
    policies=(
        *(
            CapabilityPolicyRule(
                key=key,
                level=CapabilityLevel.UNSUPPORTED,
                message=_DESCENDING_MESSAGE,
                consumer=PolicyConsumer.GATE,
                action=PolicyAction.BLOCK,
                information=QualifiedInformationKey(FAMILY_SCOPE, key, InformationLayer.NATIVE),
                applicability=unbounded,
                issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
            )
            for key in _DESCENDING_KEYS
        ),
    ),
)
