"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region, unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain,
    QualifiedInformationKey, Selector,
)
from mountainash.core.capabilities.predicates import WINDOW_ROOT
from mountainash.core.capabilities.schema import (
    CapabilityIssueClass, CapabilityLevel, Clause, ClauseOp, InformationLayer, PolicyAction,
    PolicyConsumer, Predicate,
)
from mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pandas._scope import SCOPE
from mountainash.expressions.backends.capabilities.narwhals.family._scope import SCOPE as FAMILY_SCOPE
from mountainash.expressions.core.expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW

_FLOAT_RANK_MESSAGE = (
    "Backlog 367: pandas `rank` returns float64, so row_number/rank/dense_rank "
    "values are floats (1.0, 2.0, ...) on NumPy-backed pandas; the values match "
    "other backends. No integer cast is applied: null sort keys rank as NaN, "
    "which NumPy integers cannot hold (see 252)."
)
_RANK_MESSAGE = (
    "Narwhals pandas cannot rank by several sort keys: .over(partition) accepts "
    "only elementary expressions."
)
_LAST_KEY_MESSAGE = "Narwhals pandas-like orders multi-key windows by the last key only (backlog 368)."

_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier="==2.27.1"),
    CoordinateConstraint("package", "pandas", specifier="==3.0.6"),
)),))
_LAST_KEY_APPLICABILITY = Applicability(tuple(
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
    for operation in (
        SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
        SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
        SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
    )
)
_LAST_KEY_KEYS = tuple(
    _multi_key(operation)
    for operation in (
        SUBSTRAIT_ARITHMETIC_WINDOW.LAG,
        SUBSTRAIT_ARITHMETIC_WINDOW.LEAD,
        SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE,
        SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE,
        SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE,
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
    information=(
        *(
            CapabilityInformation(
                key=CapabilityKey(function_key, "*"),
                layer=InformationLayer.NATIVE,
                # Ranking works; only the result dtype differs. Not a refusal or policy.
                level=CapabilityLevel.EXPR_CAPABLE,
                message=_FLOAT_RANK_MESSAGE,
                applicability=_APPLICABILITY,
            )
            for function_key in (
                SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
                SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
                SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
            )
        ),
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
                applicability=_LAST_KEY_APPLICABILITY,
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
                applicability=_LAST_KEY_APPLICABILITY,
                issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
            )
            for key in _LAST_KEY_KEYS
        ),
    ),
)
