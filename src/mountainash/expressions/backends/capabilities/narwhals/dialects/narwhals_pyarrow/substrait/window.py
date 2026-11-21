"""Window-shape refusals for this Narwhals dialect."""

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
from mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pyarrow._scope import SCOPE
from mountainash.expressions.backends.capabilities.narwhals.family._scope import SCOPE as FAMILY_SCOPE
from mountainash.expressions.core.expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW

_DESCENDING_MESSAGE = "Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported."
_RANK_MESSAGE = (
    "Narwhals pyarrow cannot rank by several sort keys: .over(partition) accepts only elementary expressions."
)
_PARTITION_MESSAGE = (
    "Narwhals pyarrow cannot evaluate a non-aggregating window under .over(partition_by=...): "
    "only elementary aggregations are supported when partition_by is specified."
)
_PARTITION_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
    CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
)),))
_PARTITION_KEYS = tuple(
    CapabilityKey(
        operation=operation,
        subject=WINDOW_ROOT,
        selector=Selector(kind="predicate", value=Predicate(clauses=(
            Clause(path=f"{WINDOW_ROOT}.partitioned", op=ClauseOp.EQ, operand=True),
        ))),
    )
    for operation in (
        SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
        SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
        SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
        SUBSTRAIT_ARITHMETIC_WINDOW.LAG,
        SUBSTRAIT_ARITHMETIC_WINDOW.LEAD,
    )
)
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
_RANK_KEYS = tuple(
    CapabilityKey(
        operation=operation,
        subject=WINDOW_ROOT,
        selector=Selector(kind="predicate", value=Predicate(clauses=(
            Clause(path=f"{WINDOW_ROOT}.multi_key", op=ClauseOp.EQ, operand=True),
        ))),
    )
    for operation in (
        SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
        SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
        SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
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
                message=_PARTITION_MESSAGE,
                issue="NW-WIN-06",
                applicability=_PARTITION_APPLICABILITY,
            )
            for key in _PARTITION_KEYS
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
                message=_PARTITION_MESSAGE,
                consumer=PolicyConsumer.GATE,
                action=PolicyAction.BLOCK,
                information=QualifiedInformationKey(SCOPE, key, InformationLayer.NATIVE),
                applicability=_PARTITION_APPLICABILITY,
                issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
            )
            for key in _PARTITION_KEYS
        ),
    ),
)
