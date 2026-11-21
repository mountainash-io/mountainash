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
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import (
    CapabilityIssueClass,
    CapabilityLevel,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME

_SCOPE = Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-pyarrow"))
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

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    information=tuple(
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
    policies=tuple(
        CapabilityPolicyRule(
            key=key,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            information=QualifiedInformationKey(_SCOPE, key, InformationLayer.NATIVE),
            applicability=_APPLICABILITY,
            issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
        )
        for key in _KEYS
    ),
)
