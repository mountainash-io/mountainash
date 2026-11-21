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
    FKEY_SUBSTRAIT_SCALAR_STRING,
)

_SCOPE = Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-pyarrow"))
_KEY = CapabilityKey(FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE, "replacement")
_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
    CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
)),))
_MESSAGE = "Narwhals PyArrow str.replace requires a literal replacement; per-row replacements are unsupported."

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=(
        CapabilityInformation(
            key=_KEY,
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            message=_MESSAGE,
            workaround="Use a literal string value instead of a column reference",
            issue="NW-STR-03",
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
