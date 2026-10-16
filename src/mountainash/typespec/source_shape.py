"""Schema-only structural evidence extracted from supported table carriers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mountainash.core.dtypes import DecimalDtype, MountainashDtype, TypeTarget, registry
from mountainash.core.dtypes.errors import UnknownDtypeError

from mountainash.core.types import (
    is_ibis_table,
    is_narwhals_dataframe,
    is_narwhals_lazyframe,
    is_pandas_dataframe,
    is_polars_dataframe,
    is_polars_lazyframe,
    is_pyarrow_table,
)



@dataclass(frozen=True)
class SourceShape:
    """Recursive type evidence exposed by a native schema."""

    canonical_type: MountainashDtype | None
    item_shape: SourceShape | None = None
    struct_fields: tuple[tuple[str, SourceShape], ...] = ()
    decimal: DecimalDtype | None = None

    def __post_init__(self) -> None:
        if self.decimal is not None and (
            self.canonical_type is not None or self.item_shape is not None or self.struct_fields
        ):
            raise ValueError("a decimal shape is a scalar leaf")
        if self.item_shape is not None and self.canonical_type is not MountainashDtype.LIST:
            raise ValueError("only LIST can have item_shape")
        if self.struct_fields and self.canonical_type is not MountainashDtype.STRUCT:
            raise ValueError("only STRUCT can have struct_fields")
        if self.item_shape is not None and self.struct_fields:
            raise ValueError("one source shape cannot have item and struct children")
        names = tuple(name for name, _ in self.struct_fields)
        if len(names) != len(set(names)):
            raise ValueError("struct field names must be unique")


def _resolve(native: Any, target: TypeTarget) -> Any:
    try:
        return registry.from_native(native, target=target)
    except UnknownDtypeError:
        return None

def _shape_from_dtype(dtype: Any) -> SourceShape:
    """Project the canonical detailed dtype to evidence needed by consumers."""
    from mountainash.core.dtypes import (
        ArrayDtype,
        ListDtype,
        NativeDtype,
        StructDtype,
        dtype_family,
    )

    if dtype is None:
        return SourceShape(None)
    if isinstance(dtype, DecimalDtype):
        return SourceShape(None, decimal=dtype)
    family = dtype_family(dtype)
    canonical = family if isinstance(family, MountainashDtype) else None
    if isinstance(dtype, (ListDtype, ArrayDtype)):
        child = _shape_from_dtype(dtype.element)
        if isinstance(dtype, ArrayDtype) and isinstance(dtype.dimensions, tuple):
            for _ in dtype.dimensions[1:]:
                child = SourceShape(MountainashDtype.LIST, child)
        return SourceShape(canonical, child)
    if isinstance(dtype, StructDtype):
        fields = (
            ()
            if not isinstance(dtype.fields, tuple)
            else tuple((name, _shape_from_dtype(child)) for name, child in dtype.fields)
        )
        return SourceShape(canonical, struct_fields=fields)
    if isinstance(dtype, NativeDtype):
        return SourceShape(canonical)
    return SourceShape(canonical)


def _from_schema(schema: Any, target: TypeTarget) -> dict[str, SourceShape]:
    return {
        name: _shape_from_dtype(_resolve(dtype, target))
        for name, dtype in schema.items()
    }


def _from_polars_schema(schema: Any) -> dict[str, SourceShape]:
    return _from_schema(schema, TypeTarget.POLARS)


def _from_pyarrow_schema(schema: Any) -> dict[str, SourceShape]:
    return _from_schema(
        {field.name: field for field in schema}, TypeTarget.PYARROW
    )


def _from_pandas_dtypes(dtypes: Any) -> dict[str, SourceShape]:
    return _from_schema(dtypes, TypeTarget.PANDAS)


def _from_ibis_schema(schema: Any) -> dict[str, SourceShape]:
    return _from_schema(
        {name: schema[name] for name in schema.names}, TypeTarget.IBIS
    )


def _from_narwhals_schema(native: Any) -> dict[str, SourceShape]:
    underlying = native.to_native()
    if (
        is_pandas_dataframe(underlying) or is_pyarrow_table(underlying)
        or is_polars_dataframe(underlying) or is_polars_lazyframe(underlying)
    ):
        return extract_source_shapes(underlying)
    return _from_schema(native.schema, TypeTarget.NARWHALS)


def extract_source_shapes(native: Any) -> dict[str, SourceShape]:
    """Extract recursive source shapes using schema metadata only."""
    if is_polars_dataframe(native) or is_polars_lazyframe(native):
        return _from_polars_schema(native.collect_schema())
    if is_pyarrow_table(native):
        return _from_pyarrow_schema(native.schema)
    if is_pandas_dataframe(native):
        return _from_pandas_dtypes(native.dtypes)
    if is_ibis_table(native) and type(native).__name__ == "Table":
        return _from_ibis_schema(native.schema())
    if is_narwhals_dataframe(native) or is_narwhals_lazyframe(native):
        return _from_narwhals_schema(native)
    raise TypeError(
        "extract_source_shapes: unsupported schema carrier "
        f"{type(native).__module__}.{type(native).__qualname__}"
    )


__all__ = ["SourceShape", "extract_source_shapes"]
