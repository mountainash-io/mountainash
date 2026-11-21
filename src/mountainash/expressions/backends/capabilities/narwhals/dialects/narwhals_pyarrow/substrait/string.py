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
from mountainash.core.capabilities.schema import (
    CapabilityIssueClass,
    CapabilityLevel,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
)
from mountainash.expressions.backends.capabilities.narwhals.dialects.narwhals_pyarrow._scope import SCOPE
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)

_KEYS = (
    CapabilityKey(FKEY_SUBSTRAIT_SCALAR_STRING.REPLACE, "replacement"),
    CapabilityKey(FKEY_SUBSTRAIT_SCALAR_STRING.REGEXP_REPLACE, "replacement"),
    CapabilityKey(FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS, "substring"),
    CapabilityKey(FKEY_SUBSTRAIT_SCALAR_STRING.STARTS_WITH, "substring"),
    CapabilityKey(FKEY_SUBSTRAIT_SCALAR_STRING.ENDS_WITH, "substring"),
)
_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
    CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
)),))
_MESSAGE = (
    "Narwhals PyArrow string methods accept only literal str values for this "
    "argument; column-valued (per-row) arguments are unsupported."
)

SEGMENT = CapabilitySegment(
    domain=Domain.STRING,
    information=tuple(
        CapabilityInformation(
            key=key,
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.LITERAL_ONLY,
            message=_MESSAGE,
            workaround="Use a literal string value instead of a column reference",
            issue="NW-STR-03",
            applicability=_APPLICABILITY,
        )
        for key in _KEYS
    ),
    policies=tuple(
        CapabilityPolicyRule(
            key=key,
            level=CapabilityLevel.LITERAL_ONLY,
            message=_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            information=QualifiedInformationKey(SCOPE, key, InformationLayer.NATIVE),
            applicability=_APPLICABILITY,
            issue_classes=frozenset({CapabilityIssueClass.ARGUMENT_CONTRACT}),
        )
        for key in _KEYS
    ),
)
