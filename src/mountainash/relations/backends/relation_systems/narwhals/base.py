"""Narwhals relation system — base class with backend type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.backends.expression_systems.narwhals.base import _identify_native_issue
from mountainash.relations.backends.relation_systems.base import BaseRelationSystem
from mountainash.relations.core.materialization import ExecutionForm

if TYPE_CHECKING:
    from collections.abc import Callable

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
        if frame.implementation.is_pandas():
            # An index is not data; to_arrow() would emit a named index as a column.
            # Pandas schema metadata is not data either: consumers that rebuild a
            # pandas frame from it (Ibis SQLite registration) would revive
            # ArrowDtype/pd.NA columns the destination cannot bind.
            import pyarrow as pa

            native_frame = frame.to_native()
            table = pa.Table.from_pandas(native_frame, preserve_index=False).replace_schema_metadata(None)
            if table.num_rows == 0:
                # An empty object column has no values to infer from; Arrow reports
                # null, Polars' pandas import reports String. Keep the latter.
                for index, field in enumerate(table.schema):
                    if pa.types.is_null(field.type) and native_frame[field.name].dtype == object:
                        table = table.set_column(
                            index, field.with_type(pa.string()),
                            table.column(index).cast(pa.string()),
                        )
            return table
        return frame.to_arrow()

    def check_import(
        self, arrow: pa.Table | Callable[[], pa.Table], *, location: ExecutionLocation,
    ) -> None:
        impl = (location.dialect or "").removeprefix("narwhals-")
        if impl in ("duckdb", "dask"):
            raise ValueError(
                f"eager Arrow import unsupported for lazy-only narwhals implementation {location.dialect!r}"
            )

    def import_into(
        self, arrow: pa.Table, *, location: ExecutionLocation, owned: bool = False,
    ) -> Imported:
        import narwhals as nw

        self.check_import(arrow, location=location)
        from mountainash.relations.core.execution.metadata import Imported

        impl = (location.dialect or "").removeprefix("narwhals-")
        if impl == "lazy":
            return Imported(nw.from_arrow(arrow, backend="polars").lazy())
        if impl in ("pandas", "polars", "pyarrow"):
            # Narwhals' own conversion: pandas gets NumPy-backed columns, so an
            # imported operand mixes with the caller's pandas frames. That
            # representation turns an integer column with nulls into float,
            # NaN and null into NaN, and decimals into objects.
            frame = nw.from_arrow(arrow, backend=impl)
            return Imported(frame.lazy() if location.form is ExecutionForm.LAZY else frame)
        raise ValueError(f"unknown narwhals dialect: {location.dialect!r}")

    def native_scan_eligible(self, resource: Any, *, location: ExecutionLocation | None = None) -> bool:
        if resource.data is not None or resource.path is None:
            return False
        return self._native_scan_for(resource, resource.to_dialect(), location=location)
