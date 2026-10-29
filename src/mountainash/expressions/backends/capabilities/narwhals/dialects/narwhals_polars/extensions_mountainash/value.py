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

_SCOPE = Scope(CONST_BACKEND.NARWHALS, Dialect("narwhals-polars"))
_KEY = CapabilityKey(FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST, "*")
_MESSAGE = (
    "Narwhals cannot express decimal casts natively: no round mode (narwhals#3698) and no non-strict cast (narwhals#3702)."
)

SEGMENT = CapabilitySegment(
    domain=Domain.VALUE,
    information=(
        CapabilityInformation(
            key=_KEY,
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message=_MESSAGE,
            issue="NW-MATH-11",
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST, "failure_behavior"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            message="Narwhals Expr.cast has no non-strict option (narwhals#3702).",
            issue="NW-CAST-01",
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
