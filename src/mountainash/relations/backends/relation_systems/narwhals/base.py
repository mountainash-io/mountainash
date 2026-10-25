"""Narwhals relation system — base class with backend type."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.backends.expression_systems.narwhals.base import _identify_native_issue
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem
from mountainash.relations.core.materialization import ExecutionForm

if TYPE_CHECKING:
    from mountainash.relations.core.execution.location import ExecutionLocation


class NarwhalsBaseRelationSystem(BaseRelationSystem):
    """Base mixin that identifies this relation system as Narwhals."""

    BACKEND_NAME = "narwhals"
    identify_native_issue = staticmethod(_identify_native_issue)

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.NARWHALS

    def infer_row_index_names(
        self, input_names: tuple[str, ...], *, name: str,
        location: ExecutionLocation,
    ) -> tuple[str, ...] | None:
        """Eager Narwhals prepends the ordinal; other forms are unproven.

        An existing name is a native duplicate.
        """
        if location.form is not ExecutionForm.EAGER or name in input_names:
            return None
        return (name, *input_names)

    def infer_cross_join_names(
        self, left_names: tuple[str, ...], right_names: tuple[str, ...], *,
        suffix: str, location: ExecutionLocation,
    ) -> tuple[str, ...] | None:
        return self._cross_join_names(left_names, right_names, suffix)
