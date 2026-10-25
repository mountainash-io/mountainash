"""Multi-key window refusals for Narwhals pandas."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region, unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
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
from mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pandas._scope import SCOPE
from mountainash.expressions.backends.capabilities.narwhals.family._scope import SCOPE as FAMILY_SCOPE
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_WINDOW

_RANK_MESSAGE = (
    "Narwhals pandas cannot rank by several sort keys: .over(partition) accepts "
    "only elementary expressions."
)
_LAST_KEY_MESSAGE = "Narwhals pandas-like orders multi-key windows by the last key only (backlog 368)."
_APPLICABILITY = Applicability(tuple(
    Region((
        CoordinateConstraint("package", "narwhals", specifier="==2.27.1"),
        CoordinateConstraint("package", "pandas", specifier=f"=={version}"),
    ))
    for version in ("3.0.6", "3.1.0")
))


def _multi_key(operation) -> CapabilityKey:
    return CapabilityKey(
        operation=operation,
        subject=WINDOW_ROOT,
        selector=Selector(kind="predicate", value=Predicate(clauses=(
            Clause(path=f"{WINDOW_ROOT}.multi_key", op=ClauseOp.EQ, operand=True),
        ))),
    )


_RANK_KEYS = tuple(
    _multi_key(operation)
    for operation in (FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE, FKEY_MOUNTAINASH_WINDOW.RANK_MAX)
)
_LAST_KEY_KEYS = tuple(
    _multi_key(operation)
    for operation in (
        FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
        FKEY_MOUNTAINASH_WINDOW.CUM_MAX,
        FKEY_MOUNTAINASH_WINDOW.CUM_MIN,
        FKEY_MOUNTAINASH_WINDOW.CUM_COUNT,
        FKEY_MOUNTAINASH_WINDOW.CUM_PROD,
        FKEY_MOUNTAINASH_WINDOW.DIFF,
        FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL,
        FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL,
    )
)

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
        FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
        FKEY_MOUNTAINASH_WINDOW.CUM_MAX,
        FKEY_MOUNTAINASH_WINDOW.CUM_MIN,
        FKEY_MOUNTAINASH_WINDOW.CUM_COUNT,
        FKEY_MOUNTAINASH_WINDOW.CUM_PROD,
        FKEY_MOUNTAINASH_WINDOW.DIFF,
        FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL,
        FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL,
    )
)

SEGMENT = CapabilitySegment(
    domain=Domain.WINDOW,
    changes=(),
    information=(
        *(
            CapabilityInformation(
                key=key,
                layer=InformationLayer.NATIVE,
                level=CapabilityLevel.UNSUPPORTED,
                message=_RANK_MESSAGE,
                applicability=unbounded,
            )
            for key in _RANK_KEYS
        ),
        *(
            CapabilityInformation(
                key=key,
                layer=InformationLayer.NATIVE,
                level=CapabilityLevel.UNSUPPORTED,
                message=_LAST_KEY_MESSAGE,
                issue="NW-WIN-05",
                applicability=_APPLICABILITY,
            )
            for key in _LAST_KEY_KEYS
        ),
    ),
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
        *(
            CapabilityPolicyRule(
                key=key,
                level=CapabilityLevel.UNSUPPORTED,
                message=_RANK_MESSAGE,
                consumer=PolicyConsumer.GATE,
                action=PolicyAction.BLOCK,
                information=QualifiedInformationKey(SCOPE, key, InformationLayer.NATIVE),
                applicability=unbounded,
                issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
            )
            for key in _RANK_KEYS
        ),
        *(
            CapabilityPolicyRule(
                key=key,
                level=CapabilityLevel.UNSUPPORTED,
                message=_LAST_KEY_MESSAGE,
                consumer=PolicyConsumer.GATE,
                action=PolicyAction.BLOCK,
                information=QualifiedInformationKey(SCOPE, key, InformationLayer.NATIVE),
                applicability=_APPLICABILITY,
                issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
            )
            for key in _LAST_KEY_KEYS
        ),
    ),
)
