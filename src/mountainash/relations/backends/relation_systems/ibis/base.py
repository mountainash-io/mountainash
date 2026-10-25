"""Ibis relation system — base class with backend type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem

if TYPE_CHECKING:
    from mountainash.core.dtypes.protocols import ResolvedType
    from mountainash.relations.core.execution.location import ExecutionLocation


class IbisBaseRelationSystem(BaseRelationSystem):
    """Base mixin that identifies this relation system as Ibis."""

    BACKEND_NAME = "ibis"

    @property
    def backend_type(self) -> CONST_BACKEND:
        return CONST_BACKEND.IBIS

    def describe_output_schema(
        self, native: Any, *, location: ExecutionLocation,
    ) -> dict[str, ResolvedType]:
        """Physical output types of a bound SQL relation; logical types otherwise.

        A relation whose location has a bound connection with a physical
        technique is described by that engine. Any other Ibis relation (unbound,
        in-memory, or an engine without a technique) reports its logical schema
        through the shared implementation.
        """
        from mountainash.relations.backends.relation_systems.ibis.schema_metadata import (
            describe_physical_output,
        )

        physical = describe_physical_output(native, location)
        if physical is None:
            return super().describe_output_schema(native, location=location)
        return physical

    def infer_row_index_names(
        self, input_names: tuple[str, ...], *, name: str,
        location: ExecutionLocation,
    ) -> tuple[str, ...] | None:
        """Ibis appends the ordinal, replacing an existing column in place.

        Needs a resolved dialect; Ibis-Polars has no row-index support.
        """
        if location.dialect in (None, "ibis-polars"):
            return None
        return input_names if name in input_names else (*input_names, name)

    def infer_cross_join_names(
        self, left_names: tuple[str, ...], right_names: tuple[str, ...], *,
        suffix: str, location: ExecutionLocation,
    ) -> tuple[str, ...] | None:
        """Ibis supplies its own ``_right`` suffix when none is given."""
        return self._cross_join_names(left_names, right_names, suffix or "_right")
