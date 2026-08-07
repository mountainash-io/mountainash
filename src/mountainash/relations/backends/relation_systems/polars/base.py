"""Polars relation system — base class with backend type."""

from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.capabilities.polars import (
    POLARS_REL_CAPABILITIES,
)
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem


class PolarsBaseRelationSystem(BaseRelationSystem):
    """Base mixin that identifies this relation system as Polars."""

    BACKEND_NAME = "polars"

    CAPABILITIES: tuple[CapabilityFact, ...] = POLARS_REL_CAPABILITIES

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.POLARS
