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
    FKEY_MOUNTAINASH_SCALAR_STRING,
)

_SCOPE = Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-pyarrow"))
_KEY = CapabilityKey(FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS, "pattern")
_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier="==2.27.1"),
    CoordinateConstraint("package", "pyarrow", specifier="==26.0.0"),
)),))
_MESSAGE = "Narwhals PyArrow regex matching requires a literal pattern; per-row patterns are unsupported."

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(
        CapabilityInformation(
            key=_KEY,
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            message=_MESSAGE,
            issue="NW-STR-08",
            applicability=_APPLICABILITY,
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=_KEY,
            level=CapabilityLevel.LITERAL_ONLY,
            message=_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            information=QualifiedInformationKey(_SCOPE, _KEY, InformationLayer.NATIVE),
            applicability=_APPLICABILITY,
            issue_classes=frozenset({CapabilityIssueClass.ARGUMENT_CONTRACT}),
        ),
    ),
)
