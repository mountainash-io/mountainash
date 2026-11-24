"""Calendar-offset refusals for Narwhals on PyArrow."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import Applicability, CoordinateConstraint, Region
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    QualifiedInformationKey,
    Selector,
)
from mountainash.core.capabilities.schema import (
    CapabilityIssueClass,
    CapabilityLevel,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
)
from mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pyarrow._scope import SCOPE
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME

_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
    CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
)),))
_MESSAGE = "Narwhals does not support year/month offsets for PyArrow datetimes (dt.offset_by raises NotImplementedError)."
_KEYS = tuple(
    CapabilityKey(operation, "*")
    for operation in (
        FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS,
        FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS,
    )
)

_UNIT_MESSAGE = (
    "Narwhals dt.offset_by raises NotImplementedError for month and year offsets on "
    "PyArrow datetimes, so calendar-unit round and ceil (year, quarter, month) are unsupported."
)
_UNIT_KEYS = tuple(
    CapabilityKey(operation, "unit", Selector(kind="exact", value=unit))
    for operation in (
        FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
        FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
    )
    for unit in ("1y", "1mo", "1q", "year", "month", "quarter")
)

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    information=(
        *(
            CapabilityInformation(
                key=key,
                layer=InformationLayer.NATIVE,
                level=CapabilityLevel.UNSUPPORTED,
                message=_MESSAGE,
                issue="NW-DT-08",
                applicability=_APPLICABILITY,
            )
            for key in _KEYS
        ),
        *(
            CapabilityInformation(
                key=key,
                layer=InformationLayer.NATIVE,
                level=CapabilityLevel.UNSUPPORTED,
                message=_UNIT_MESSAGE,
                issue="NW-DT-08",
                applicability=_APPLICABILITY,
            )
            for key in _UNIT_KEYS
        ),
        CapabilityInformation(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY, "*"),
            layer=InformationLayer.NATIVE,
            # Fixed-width offsets work; only the month/year units are refused,
            # and no predicate can see the offset text, so there is no gate.
            level=CapabilityLevel.EXPR_CAPABLE,
            message=(
                "Narwhals dt.offset_by raises NotImplementedError for month and "
                "year offsets ('..mo', '..y') on PyArrow datetimes; fixed-width "
                "units (d, h, m, s, ms, us) work. No runtime refusal is applied."
            ),
            issue="NW-DT-08",
            applicability=_APPLICABILITY,
        ),
    ),
    policies=tuple(
        CapabilityPolicyRule(
            key=key,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            information=QualifiedInformationKey(SCOPE, key, InformationLayer.NATIVE),
            applicability=_APPLICABILITY,
            issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
        )
        for key in _KEYS
    ) + tuple(
        CapabilityPolicyRule(
            key=key,
            level=CapabilityLevel.UNSUPPORTED,
            message=_UNIT_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            information=QualifiedInformationKey(SCOPE, key, InformationLayer.NATIVE),
            applicability=_APPLICABILITY,
            issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
        )
        for key in _UNIT_KEYS
    ),
)
