"""Narwhals relation system — base class with backend type."""

from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND


class NarwhalsBaseRelationSystem:
    """Base mixin that identifies this relation system as Narwhals."""

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.NARWHALS
