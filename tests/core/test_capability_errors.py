"""BackendCapabilityError renders metadata carried by a published policy."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    QualifiedInformationKey,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import InformationLayer, PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR

_SCOPE = Scope(CONST_BACKEND.POLARS, Dialect("polars"))


def test_error_formats_policy_information_workaround_and_issue():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        key = CapabilityKey(FK_STR.LPAD, "characters")
        information = CapabilityInformation(
            key, InformationLayer.PUBLIC, CapabilityLevel.LITERAL_ONLY, "2026-09-18",
            "fill character limitation", workaround="Use a literal fill character", issue="PL-STR-01",
        )
        policy = CapabilityPolicyRule(
            key, CapabilityLevel.LITERAL_ONLY, "2026-09-18", "literal fill required",
            PolicyConsumer.GATE, PolicyAction.BLOCK,
            information=QualifiedInformationKey(_SCOPE, key, InformationLayer.PUBLIC),
        )
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.polars.dialects.polars.substrait.string",
            _SCOPE, CapabilitySegment(Domain.STRING, information=(information,), policies=(policy,)),
        ))
        limitation = CapabilityRegistry.capability_for(FK_STR.LPAD, "characters", CONST_BACKEND.POLARS, "polars")
        error = BackendCapabilityError(policy.message, backend="polars", function_key=FK_STR.LPAD, limitation=limitation)
        text = str(error)
        assert "[polars]" in text
        assert "Workaround: Use a literal fill character" in text
        assert "Upstream ref: PL-STR-01" in text
        assert error.limitation is limitation
    finally:
        CapabilityRegistry.restore(snapshot)
