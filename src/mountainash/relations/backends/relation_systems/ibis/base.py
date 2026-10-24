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
