"""Polars relation system — base class with backend type."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem

if TYPE_CHECKING:
    from mountainash.relations.core.execution.location import ExecutionLocation


class PolarsBaseRelationSystem(BaseRelationSystem):
    """Base mixin that identifies this relation system as Polars."""

    BACKEND_NAME = "polars"

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.POLARS

    def infer_row_index_names(
        self, input_names: tuple[str, ...], *, name: str,
        location: ExecutionLocation,
    ) -> tuple[str, ...] | None:
        """Polars prepends the ordinal; an existing name is a native duplicate."""
        return None if name in input_names else (name, *input_names)

    def infer_cross_join_names(
        self, left_names: tuple[str, ...], right_names: tuple[str, ...], *,
        suffix: str, location: ExecutionLocation,
    ) -> tuple[str, ...] | None:
        return self._cross_join_names(left_names, right_names, suffix)
