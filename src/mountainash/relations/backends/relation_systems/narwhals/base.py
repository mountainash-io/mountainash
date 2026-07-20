"""Narwhals relation system — base class with backend type."""

from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)


class NarwhalsBaseRelationSystem(BaseRelationSystem):
    """Base mixin that identifies this relation system as Narwhals."""

    BACKEND_NAME = "narwhals"

    CAPABILITIES: tuple[CapabilityFact, ...] = (
        CapabilityFact(
            operation_key=RKEY_MOUNTAINASH_REL.UNNEST, param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.NARWHALS,
            message="unnest() is not supported by the Narwhals backend",
            workaround="Use the Polars backend for unnest.",
            since="2026-07-05",
        ),
        CapabilityFact(
            operation_key=RKEY_MOUNTAINASH_REL.JOIN_ASOF, param="tolerance",
            level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.NARWHALS,
            message="join_asof(tolerance=...) is not supported by the Narwhals backend",
            workaround="Drop tolerance= or use the Polars backend.",
            since="2026-07-05",
            condition="tolerance is not None",
        ),
        CapabilityFact(
            operation_key=RKEY_MOUNTAINASH_REL.READ_RESOURCE, param="resource",
            level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.NARWHALS,
            message="CSV dialect field 'escape_char' is not native-safe on this backend's "
                    "reader — routed to the CsvSpec fallback reader",
            workaround="none needed — mountainash routes automatically",
            since="2026-07-05",
            condition="resource.dialect.escape_char is set",
            probe_exempt="router, not gate — fallback handles it; behaviour covered by relations resource tests",
        ),
    )

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.NARWHALS


CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, NarwhalsBaseRelationSystem.CAPABILITIES)
