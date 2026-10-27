"""Narwhals relation system — base class with backend type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.backends.expression_systems.narwhals.base import _identify_native_issue
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem
from mountainash.relations.core.materialization import ExecutionForm

if TYPE_CHECKING:
    import pyarrow as pa

    from mountainash.relations.core.execution.metadata import Imported
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

    def export(self, native: Any, *, source: ExecutionLocation) -> pa.Table:
        import narwhals as nw

        frame = nw.from_native(native)
        if isinstance(frame, nw.LazyFrame):
            frame = frame.collect()
        return frame.to_arrow()

    def check_import(self, arrow: pa.Table, *, location: ExecutionLocation) -> None:
        return None

    def import_into(
        self, arrow: pa.Table, *, location: ExecutionLocation, owned: bool = False,
    ) -> Imported:
        import narwhals as nw

        from mountainash.core.errors import BackendConversionError
        from mountainash.relations.core.execution.metadata import Imported

        impl = (location.dialect or "").removeprefix("narwhals-")
        if impl == "lazy":
            return Imported(nw.from_arrow(arrow, backend="polars").lazy())
        if impl in ("pandas", "polars", "pyarrow"):
            return Imported(nw.from_arrow(arrow, backend=impl))
        if impl in ("duckdb", "dask"):
            reason = "eager Arrow import unsupported for lazy-only narwhals implementation"
            raise BackendConversionError(
                reason,
                boundary_key=None,
                source_family="arrow",
                source_dialect=None,
                destination_family=str(location.family),
                destination_dialect=location.dialect,
                source_type="pyarrow.Table",
                route="import_into",
                reason=reason,
            )
        raise ValueError(f"unknown narwhals dialect: {location.dialect!r}")

    def native_scan_eligible(self, resource: Any, *, location: ExecutionLocation | None = None) -> bool:
        return self._native_scan_for(resource, resource.to_dialect())
