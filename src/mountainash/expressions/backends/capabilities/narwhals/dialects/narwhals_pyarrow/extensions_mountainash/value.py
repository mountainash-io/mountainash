"""Qualified provider restriction, separate from ordinary backend lowering."""

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
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_VALUE,
)

_SCOPE = Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-pyarrow"))
_KEY = CapabilityKey(FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST, "*")
_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier="==2.27.1"),
    CoordinateConstraint("package", "pyarrow", specifier="==26.0.0"),
)),))
_MESSAGE = "Mountainash has no Narwhals PyArrow Decimal conversion implementation; rounding and non-strict cast limitations are tracked by narwhals#3698 and #3702."

SEGMENT = CapabilitySegment(
    domain=Domain.VALUE,
    information=(
        CapabilityInformation(
            key=_KEY,
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            issue="NW-MATH-11",
            applicability=_APPLICABILITY,
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=_KEY,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            information=QualifiedInformationKey(_SCOPE, _KEY, InformationLayer.PUBLIC),
            applicability=_APPLICABILITY,
            issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
        ),
    ),
)
