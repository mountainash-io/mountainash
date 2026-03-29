"""Ibis relation system — base class with backend type."""

from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND


class IbisBaseRelationSystem:
    """Base mixin that identifies this relation system as Ibis."""

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.IBIS
