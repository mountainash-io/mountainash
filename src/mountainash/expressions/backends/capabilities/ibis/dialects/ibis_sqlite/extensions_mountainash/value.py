"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
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
    CapabilityLevel,
    InformationLayer,
    PolicyAction,
    PolicyConsumer,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_VALUE,
)

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite"))
_KEY = CapabilityKey(FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST, "*")
_MESSAGE = (
    "SQLite has no fixed-precision decimal type; Ibis lowers decimal to REAL."
)

SEGMENT = CapabilitySegment(
    domain=Domain.VALUE,
    information=(
        CapabilityInformation(
            key=_KEY,
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            applicability=unbounded,
        ),
    ),
    policies=(
        CapabilityPolicyRule(
            key=_KEY,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            information=QualifiedInformationKey(_SCOPE, _KEY, InformationLayer.NATIVE),
            applicability=unbounded,
        ),
    ),
)
