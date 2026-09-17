"""Narwhals relation system — base class with backend type."""

from __future__ import annotations

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem


class NarwhalsBaseRelationSystem(BaseRelationSystem):
    """Base mixin that identifies this relation system as Narwhals."""

    BACKEND_NAME = "narwhals"

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.NARWHALS
