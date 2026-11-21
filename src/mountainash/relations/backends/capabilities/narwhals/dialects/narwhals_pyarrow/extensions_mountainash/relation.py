"""Scope-owned capability declarations; import-safe data only."""

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
from mountainash.relations.backends.capabilities.narwhals.dialects.narwhals_pyarrow._scope import SCOPE
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

_APPLICABILITY = Applicability((Region((
    CoordinateConstraint("package", "narwhals", specifier=">=2.27.1"),
    CoordinateConstraint("package", "pyarrow", specifier=">=26.0.0"),
)),))

_JOIN_ASOF_KEY = CapabilityKey(operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF, subject="*")
_JOIN_ASOF_MESSAGE = "Narwhals has no join_asof implementation for the PyArrow backend."
_PIVOT_KEY = CapabilityKey(operation=RKEY_MOUNTAINASH_REL.PIVOT, subject="*")
_PIVOT_MESSAGE = "Narwhals has no pivot implementation for the PyArrow backend."

_DECLARATIONS = (
    (_JOIN_ASOF_KEY, _JOIN_ASOF_MESSAGE, "NW-REL-06", "Use the Polars backend for join_asof."),
    (_PIVOT_KEY, _PIVOT_MESSAGE, "NW-REL-07", "Use the Polars or pandas backend for pivot."),
)

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    information=tuple(
        CapabilityInformation(
            key=key,
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message=message,
            workaround=workaround,
            issue=issue,
            applicability=_APPLICABILITY,
        )
        for key, message, issue, workaround in _DECLARATIONS
    ),
    policies=tuple(
        CapabilityPolicyRule(
            key=key,
            level=CapabilityLevel.UNSUPPORTED,
            message=message,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            information=QualifiedInformationKey(SCOPE, key, InformationLayer.NATIVE),
            applicability=_APPLICABILITY,
            issue_classes=frozenset({CapabilityIssueClass.AVAILABILITY}),
        )
        for key, message, _issue, _workaround in _DECLARATIONS
    ),
)
