"""Schema-only structural evidence extracted from supported table carriers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mountainash.core.dtypes import MountainashDtype, TypeTarget, registry
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


_NUMERIC_CANONICALS = frozenset(
    dtype
    for dtype in MountainashDtype
    if dtype.name.startswith(("I", "U", "FP"))
)


@dataclass(frozen=True)
class SourceShape:
    """Recursive type evidence exposed by a native schema."""

    canonical_type: MountainashDtype | None
    item_shape: SourceShape | None = None
    struct_fields: tuple[tuple[str, SourceShape], ...] = ()

    def __post_init__(self) -> None:
        if self.item_shape is not None and self.canonical_type is not MountainashDtype.LIST:
            raise ValueError("only LIST can have item_shape")
        if self.struct_fields and self.canonical_type is not MountainashDtype.STRUCT:
            raise ValueError("only STRUCT can have struct_fields")
        if self.item_shape is not None and self.struct_fields:
            raise ValueError("one source shape cannot have item and struct children")
        names = tuple(name for name, _ in self.struct_fields)
        if len(names) != len(set(names)):
            raise ValueError("struct field names must be unique")


def _canonical(native: Any, target: TypeTarget) -> MountainashDtype | None:
    try:
        return registry.from_native(native, target=target)
    except (UnknownDtypeError, TypeError, ValueError):
        return None


def _from_polars_dtype(dtype: Any, pl: Any) -> SourceShape:
    canonical = _canonical(dtype, TypeTarget.POLARS)
    if canonical is MountainashDtype.LIST:
        inner = getattr(dtype, "inner", None)
        return SourceShape(MountainashDtype.LIST, _from_polars_dtype(inner, pl))
    if canonical is MountainashDtype.STRUCT:
        fields = tuple(
            (field.name, _from_polars_dtype(field.dtype, pl))
            for field in getattr(dtype, "fields", ())
        )
        return SourceShape(MountainashDtype.STRUCT, struct_fields=fields)
    return SourceShape(canonical)


def _from_polars_schema(schema: Any) -> dict[str, SourceShape]:
    from mountainash.core.lazy_imports import import_polars

    pl = import_polars()
    return {name: _from_polars_dtype(dtype, pl) for name, dtype in schema.items()}


def _is_pyarrow_list(dtype: Any, pa: Any) -> bool:
    return any(
        checker(dtype)
        for name in ("is_list", "is_large_list", "is_fixed_size_list", "is_list_view", "is_large_list_view")
        if (checker := getattr(pa.types, name, None)) is not None
    )


def _from_pyarrow_dtype(dtype: Any, pa: Any) -> SourceShape:
    canonical = _canonical(dtype, TypeTarget.PYARROW)
    if _is_pyarrow_list(dtype, pa):
        return SourceShape(MountainashDtype.LIST, _from_pyarrow_dtype(dtype.value_type, pa))
    if pa.types.is_struct(dtype):
        fields = tuple((field.name, _from_pyarrow_dtype(field.type, pa)) for field in dtype)
        return SourceShape(MountainashDtype.STRUCT, struct_fields=fields)
    return SourceShape(canonical)


def _from_pyarrow_schema(schema: Any) -> dict[str, SourceShape]:
    from mountainash.core.lazy_imports import import_pyarrow

    pa = import_pyarrow()
    return {field.name: _from_pyarrow_dtype(field.type, pa) for field in schema}


def _from_pandas_dtype(dtype: Any) -> SourceShape:
    # pandas object is intentionally opaque. Never inspect a Series to infer it.
    if str(dtype) == "object":
        return SourceShape(None)
    arrow_dtype = getattr(dtype, "pyarrow_dtype", None)
    if arrow_dtype is not None:
        from mountainash.core.lazy_imports import import_pyarrow

        return _from_pyarrow_dtype(arrow_dtype, import_pyarrow())
    return SourceShape(_canonical(dtype, TypeTarget.PANDAS))


def _from_pandas_dtypes(dtypes: Any) -> dict[str, SourceShape]:
    return {name: _from_pandas_dtype(dtype) for name, dtype in dtypes.items()}


def _from_ibis_dtype(dtype: Any) -> SourceShape:
    canonical = _canonical(dtype, TypeTarget.IBIS)
    if canonical is MountainashDtype.LIST:
        return SourceShape(MountainashDtype.LIST, _from_ibis_dtype(getattr(dtype, "value_type", None)))
    if canonical is MountainashDtype.STRUCT:
        raw_fields = getattr(dtype, "fields", {})
        if hasattr(raw_fields, "items"):
            fields = tuple((name, _from_ibis_dtype(child)) for name, child in raw_fields.items())
        else:
            fields = tuple(
                (field.name, _from_ibis_dtype(field.type))
                for field in raw_fields
            )
        return SourceShape(MountainashDtype.STRUCT, struct_fields=fields)
    return SourceShape(canonical)


def _from_ibis_schema(schema: Any) -> dict[str, SourceShape]:
    return {name: _from_ibis_dtype(schema[name]) for name in schema.names}


def _from_narwhals_dtype(dtype: Any) -> SourceShape:
    canonical = _canonical(dtype, TypeTarget.NARWHALS)
    if canonical is MountainashDtype.LIST:
        return SourceShape(MountainashDtype.LIST, _from_narwhals_dtype(getattr(dtype, "inner", None)))
    if canonical is MountainashDtype.STRUCT:
        fields = tuple(
            (field.name, _from_narwhals_dtype(field.dtype))
            for field in getattr(dtype, "fields", ())
        )
        return SourceShape(MountainashDtype.STRUCT, struct_fields=fields)
    return SourceShape(canonical)


def _from_narwhals_schema(native: Any) -> dict[str, SourceShape]:
    underlying = native.to_native()
    if is_pandas_dataframe(underlying):
        return _from_pandas_dtypes(underlying.dtypes)
    return {name: _from_narwhals_dtype(dtype) for name, dtype in native.schema.items()}


def extract_source_shapes(native: Any) -> dict[str, SourceShape]:
    """Extract recursive source shapes using schema metadata only."""
    if is_polars_dataframe(native) or is_polars_lazyframe(native):
        return _from_polars_schema(native.collect_schema())
    if is_pyarrow_table(native):
        return _from_pyarrow_schema(native.schema)
    if is_pandas_dataframe(native):
        return _from_pandas_dtypes(native.dtypes)
    if is_ibis_table(native):
        return _from_ibis_schema(native.schema())
    if is_narwhals_dataframe(native) or is_narwhals_lazyframe(native):
        return _from_narwhals_schema(native)
    raise TypeError(
        "extract_source_shapes: unsupported schema carrier "
        f"{type(native).__module__}.{type(native).__qualname__}"
    )


__all__ = ["SourceShape", "extract_source_shapes"]
