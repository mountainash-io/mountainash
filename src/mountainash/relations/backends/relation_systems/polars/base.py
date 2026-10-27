"""Polars relation system — base class with backend type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem

if TYPE_CHECKING:
    import pyarrow as pa

    from mountainash.relations.core.execution.metadata import Imported
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

    def export(self, native: Any, *, source: ExecutionLocation) -> pa.Table:
        if hasattr(native, "collect"):
            native = native.collect()
        return native.to_arrow()

    def check_import(self, arrow: pa.Table, *, location: ExecutionLocation) -> None:
        return None

    def import_into(
        self, arrow: pa.Table, *, location: ExecutionLocation, owned: bool = False,
    ) -> Imported:
        import polars as pl

        from mountainash.relations.core.execution.metadata import Imported
        from mountainash.relations.core.materialization import ExecutionForm

        frame = pl.from_arrow(arrow)
        return Imported(frame.lazy() if location.form is ExecutionForm.LAZY else frame)

    def native_scan_eligible(self, resource: Any, *, location: ExecutionLocation | None = None) -> bool:
        if resource.data is not None or resource.path is None:
            return False
        return self._native_scan_for(resource, resource.to_dialect())
