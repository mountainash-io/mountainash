"""Version-bounded public refusal for an unavailable Ibis translator."""

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

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-mysql"))
_KEY = CapabilityKey(FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST, "*")
_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "ibis-framework", specifier="==12.0.0"),
)),))
_MESSAGE = "Ibis 12.0.0 MySQL lacks RegexReplace translation required by Decimal text normalization."

SEGMENT = CapabilitySegment(
    domain=Domain.VALUE,
    information=(
        CapabilityInformation(
            key=_KEY,
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            issue="IB-STR-14",
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
