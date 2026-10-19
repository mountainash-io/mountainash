"""
TypeSpec Converters - Convert TypeSpec to Backend-Specific Formats

Provides functions to convert TypeSpec to:
- Polars schema dict
- pandas dtypes dict
- PyArrow Schema
- Ibis schema

All converters use lazy imports and leverage the centralized type system.
"""
from __future__ import annotations

from dataclasses import replace

from typing import TYPE_CHECKING, Any, Dict, Mapping
import warnings

from mountainash.core.dtypes import (
    ArrayDtype,
    DurationDtype,
    ListDtype,
    NativeDtype,
    InvalidBackendTypeError,
    MountainashDtype,
    SchemaTypeStatus,
    StructDtype,
    TimeDtype,
    TimestampDtype,
    TypeTarget,
    UnknownDtypeError,
    resolve_dtype_parameters,
    registry,
)
from mountainash.typespec.errors import InvalidGeospatialFormatError
from mountainash.core.dtypes.errors import DtypeMappingError
from mountainash.typespec.universal_types import UniversalType, from_canonical, to_canonical

if TYPE_CHECKING:
    from .spec import FieldSpec, TypeSpec
    import pyarrow as pa


# ============================================================================
# Geospatial field-aware resolution (spec §8.3)
# ============================================================================

_GEOPOINT_FORMAT_CANONICAL: dict[str, MountainashDtype] = {
    "default": MountainashDtype.STRING,
    "array": MountainashDtype.LIST,
    "object": MountainashDtype.STRUCT,
}
_GEOJSON_FORMATS: frozenset[str] = frozenset({"default", "topojson"})


def resolve_field_canonical(
    field: "FieldSpec", *, field_name: str | None = None,
) -> Any:
    """Resolve declared canonical type with optional local diagnostic context."""
    broad = _resolve_broad_field_canonical(field, field_name=field_name)
    return field.dtype if field.dtype is not None else broad


def declared_fields(field: "FieldSpec") -> Mapping[str, "FieldSpec"]:
    """Return authored ordered object members, or project type-only members."""
    from .spec import FieldSpec

    if field.fields is not None:
        return field.fields
    dtype = resolve_field_canonical(field)
    if isinstance(dtype, StructDtype) and isinstance(dtype.fields, tuple):
        return {
            name: (
                FieldSpec(backend_type=child)
                if isinstance(child, NativeDtype)
                else FieldSpec(dtype=child)
            )
            for name, child in dtype.fields
        }
    return {}


def declared_element(field: "FieldSpec") -> "FieldSpec | None":
    """Return authored collection element, or a type-only projected element."""
    from .spec import FieldSpec

    if field.element is not None:
        return field.element
    dtype = resolve_field_canonical(field)
    if isinstance(dtype, (ListDtype, ArrayDtype)):
        child = dtype.element
        return (
            FieldSpec(backend_type=child)
            if isinstance(child, NativeDtype)
            else FieldSpec(dtype=child)
        )
    return None


def _collection_item(field: "FieldSpec", dtype: Any = None) -> "FieldSpec | None":
    """Project one runtime axis; fixed-array element metadata describes leaves."""
    from .spec import FieldSpec

    element = declared_element(field)
    dtype = resolve_field_canonical(field) if dtype is None else dtype
    if (
        element is not None and isinstance(dtype, ArrayDtype)
        and isinstance(dtype.dimensions, tuple) and len(dtype.dimensions) > 1
    ):
        return FieldSpec(element=element, dimensions=dtype.dimensions[1:])
    return element


def _with_effective_dtype(field: "FieldSpec", dtype: Any) -> "FieldSpec":
    """Attach resolved execution types without losing reusable child metadata."""
    from mountainash.core.dtypes import dtype_family
    from .spec import FieldSpec

    if dtype is None or dtype is SchemaTypeStatus.UNKNOWN:
        return field
    if isinstance(dtype, NativeDtype):
        return field.variant(backend_type=dtype)
    properties = field._constructor_properties()
    declared = resolve_field_canonical(field)
    if declared is None or declared is SchemaTypeStatus.UNKNOWN or dtype_family(declared) != dtype_family(dtype):
        properties["type"] = UniversalType.ANY
    properties["backend_type"] = getattr(dtype, "native", None)
    properties.pop("dtype", None)
    if isinstance(dtype, StructDtype) and isinstance(dtype.fields, tuple):
        children = declared_fields(field)
        properties["fields"] = {
            name: _with_effective_dtype(children.get(name, FieldSpec()), child)
            for name, child in dtype.fields
        }
    elif isinstance(dtype, (ListDtype, ArrayDtype)):
        properties["element"] = _with_effective_dtype(
            declared_element(field) or FieldSpec(), dtype.element,
        )
        properties["dimensions"] = dtype.dimensions if isinstance(dtype, ArrayDtype) else None
    else:
        properties["dtype"] = dtype
    return FieldSpec(**properties)


def _resolve_broad_field_canonical(
    field: "FieldSpec", *, field_name: str | None = None,
) -> Any:
    """Resolve authored broad semantics independently of precise refinements."""
    context = field_name if field_name is not None else "<unnamed>"
    fmt = field.format
    if field.type is UniversalType.GEOPOINT:
        if not isinstance(fmt, str) or fmt not in _GEOPOINT_FORMAT_CANONICAL:
            raise InvalidGeospatialFormatError(
                context, UniversalType.GEOPOINT, fmt, sorted(_GEOPOINT_FORMAT_CANONICAL)
            )
        return _GEOPOINT_FORMAT_CANONICAL[fmt]
    if field.type is UniversalType.GEOJSON:
        if not isinstance(fmt, str) or fmt not in _GEOJSON_FORMATS:
            raise InvalidGeospatialFormatError(
                context, UniversalType.GEOJSON, fmt, sorted(_GEOJSON_FORMATS)
            )
        return MountainashDtype.JSON
    if field.type is UniversalType.STRING and field.format == "binary":
        return MountainashDtype.BINARY
    return to_canonical(field.type)


# ============================================================================
# Shared resolution core
# ============================================================================
def _execution_type_target(family: Any) -> TypeTarget | None:
    """Translate an execution family, not a dataframe carrier, to its dtype domain."""
    if family is None:
        return None
    if family.value in ("pandas", "pyarrow", "narwhals"):
        return TypeTarget.NARWHALS
    return TypeTarget(family.value)


def _native_types_equal(left: Any, right: Any, target: TypeTarget) -> bool:
    """Compare native types in their owning domain, retaining parameters."""
    if target is TypeTarget.IBIS:
        import ibis.expr.datatypes as dt
        return dt.dtype(left) == dt.dtype(right)
    if target is TypeTarget.PANDAS:
        import pandas as pd
        return pd.api.types.pandas_dtype(left) == pd.api.types.pandas_dtype(right)
    return left == right


def _field_dtype_native(field: "FieldSpec") -> NativeDtype | None:
    native = getattr(field.dtype, "native", None)
    return native if isinstance(native, NativeDtype) else None


def _resolve_field_target(
    field: "FieldSpec", target: TypeTarget, *, emit_warning: bool = True,
    source: Any = SchemaTypeStatus.UNKNOWN, field_name: str | None = None,
) -> Any:
    """Resolve one declaration, honoring whole-field native refinements."""
    context = field_name if field_name is not None else "<unnamed>"
    declared = resolve_field_canonical(field, field_name=field_name)
    if declared is SchemaTypeStatus.UNKNOWN:
        declared = _resolve_broad_field_canonical(field, field_name=field_name)
    dtype_native = _field_dtype_native(field)
    if dtype_native is not None and not field.backend_type:
        if dtype_native.target is not target:
            raise DtypeMappingError(
                f"field {context!r}: native override belongs to {dtype_native.target}, not {target}"
            )
        return dtype_native
    override = field.backend_type
    if override is None or (isinstance(override, str) and not override):
        if isinstance(declared, StructDtype):
            children = declared_fields(field)
            if children:
                declared = replace(declared, fields=tuple(
                    (name, _resolve_field_target(
                        child, target, emit_warning=emit_warning, field_name=name,
                    ) or SchemaTypeStatus.UNKNOWN)
                    for name, child in children.items()
                ))
        elif isinstance(declared, (ListDtype, ArrayDtype)):
            element = declared_element(field)
            if element is not None:
                child = _resolve_field_target(
                    element, target, emit_warning=emit_warning, field_name=f"{context}[]",
                ) or SchemaTypeStatus.UNKNOWN
                declared = replace(declared, element=child)
        return resolve_dtype_parameters(declared, source)
    if isinstance(override, NativeDtype):
        if override.target is not target:
            raise DtypeMappingError(
                f"field {context!r}: native override belongs to {override.target}, not {target}"
            )
        effective = override
    else:
        native = registry.parse_type_string(override, target)
        if native is None:
            raise InvalidBackendTypeError(context, override, target)
        effective = NativeDtype(value=native, target=target)
    if field.dtype is not None and emit_warning:
        unverified = declared in (
            MountainashDtype.JSON, MountainashDtype.XSD_DURATION,
            MountainashDtype.XSD_YEAR, MountainashDtype.XSD_YEARMONTH,
            MountainashDtype.TIMESTAMP, MountainashDtype.DURATION,
            MountainashDtype.LIST, MountainashDtype.STRUCT,
        ) or isinstance(declared, (TimestampDtype, TimeDtype, DurationDtype,
                                   ListDtype, ArrayDtype, StructDtype))
        equivalent = False
        try:
            if not unverified:
                expected = registry.to_native_schema(declared, target)
                equivalent = _native_types_equal(expected, effective.value, target)
        except DtypeMappingError:
            unverified = True
        if not equivalent:
            reason = "equivalence unverified" if unverified else "dtype mismatch"
            warnings.warn(
                f"field {context!r} on {target.value}: {reason} between "
                f"canonical {declared!r} and native override {effective.value!r}; native override wins",
                UserWarning, stacklevel=3,
            )
    return effective





def _resolve_field_native(
    field: "FieldSpec", target: TypeTarget, *, field_name: str | None = None,
) -> Any:
    canon = _resolve_field_target(field, target, field_name=field_name)
    if isinstance(canon, NativeDtype):
        return canon.value
    if field.dtype is None and field.categories is not None and target in (TypeTarget.POLARS, TypeTarget.PANDAS):
        from mountainash.typespec._categorical import categorical_values
        values = categorical_values(field.categories)
        if target is TypeTarget.POLARS:
            from mountainash.core.lazy_imports import import_polars
            pl = import_polars()
            return pl.Enum([str(v) for v in values]) if field.categories_ordered else pl.Categorical
        import pandas as pd
        return pd.CategoricalDtype(categories=values, ordered=bool(field.categories_ordered))
    if canon is None:
        canon = MountainashDtype.STRING
    if isinstance(canon, StructDtype):
        children = declared_fields(field)
        if field.fields is not None or isinstance(canon.fields, tuple):
            return _resolve_struct_inner(
                children, target, registry.to_native_schema(MountainashDtype.STRUCT, target),
            )
    if isinstance(canon, ListDtype):
        element = declared_element(field)
        if element is not None:
            element_dtype = resolve_field_canonical(element, field_name=f"{field_name or '<unnamed>'}[]")
            if isinstance(element_dtype, StructDtype) and (
                element.fields is not None or isinstance(element_dtype.fields, tuple)
            ):
                struct_native = _resolve_struct_inner(
                    declared_fields(element), target,
                    registry.to_native_schema(MountainashDtype.STRUCT, target),
                )
                if target is TypeTarget.POLARS:
                    from mountainash.core.lazy_imports import import_polars
                    return import_polars().List(struct_native)
                if target is TypeTarget.NARWHALS:
                    from mountainash.core.lazy_imports import import_narwhals
                    return import_narwhals().List(struct_native)
                if target is TypeTarget.PYARROW:
                    from mountainash.core.lazy_imports import import_pyarrow
                    return import_pyarrow().list_(struct_native)
                if target is TypeTarget.IBIS:
                    return f"array<{struct_native}>"
    native = registry.to_native_schema(canon, target)
    if canon is MountainashDtype.LIST and field.item_type:
        return _resolve_list_inner(field_name or "<unnamed>", field.item_type, target, native)
    return native


def _resolve_struct_inner(
    fields: Mapping[str, "FieldSpec"], target: TypeTarget, bare_native: Any,
) -> Any:
    if target is TypeTarget.PANDAS:
        return bare_native
    inner_pairs = [
        (name, SchemaTypeStatus.UNKNOWN if resolve_field_canonical(child) is SchemaTypeStatus.UNKNOWN
         and child.backend_type is None else _resolve_field_native(child, target, field_name=name))
        for name, child in fields.items()
    ]
    if target is TypeTarget.POLARS:
        from mountainash.core.lazy_imports import import_polars
        pl = import_polars()
        return pl.Struct({name: pl.Null if dtype is SchemaTypeStatus.UNKNOWN else dtype
                          for name, dtype in inner_pairs})
    if target is TypeTarget.NARWHALS:
        from mountainash.core.lazy_imports import import_narwhals
        nw = import_narwhals()
        return nw.Struct({name: nw.Unknown if dtype is SchemaTypeStatus.UNKNOWN else dtype
                          for name, dtype in inner_pairs})
    if target is TypeTarget.PYARROW:
        from mountainash.core.lazy_imports import import_pyarrow
        pa = import_pyarrow()
        return pa.struct([pa.field(name, pa.null() if dtype is SchemaTypeStatus.UNKNOWN else dtype)
                          for name, dtype in inner_pairs])
    if target is TypeTarget.IBIS:
        return "struct<" + ", ".join(
            f"{name}: {'null' if dtype is SchemaTypeStatus.UNKNOWN else dtype}" for name, dtype in inner_pairs
        ) + ">"
    return bare_native




def _resolve_list_inner(
    field_name: str, item_type_str: str, target: TypeTarget, bare_native: Any
) -> Any:
    """Parameterize a bare list container with its Frictionless item_type
    (item 54, gap 2). Layered AFTER the backend_type/raise branch — a
    backend_type wins first; canonical LIST + item_type is the fallback
    enrichment, not a new top-priority branch.

    Pandas returns bare_native unchanged — no native parameterized list
    dtype, "object" is the correct, only representation.
    """
    from mountainash.typespec.universal_types import parse_universal
    try:
        item_universal = parse_universal(item_type_str)
    except UnknownDtypeError as e:
        # parse_universal raises without field context; chain it so the error
        # is traceable to its source field while keeping UnknownDtypeError
        # (the repo convention for "input not recognized as any dtype").
        raise UnknownDtypeError(
            f"field {field_name!r}: item_type {item_type_str!r} is not a "
            f"recognized UniversalType"
        ) from e
    item_canon = to_canonical(item_universal)
    if item_canon is None:  # item_type == "any" — no parameterization possible
        return bare_native
    inner_native = registry.to_native_schema(item_canon, target)
    if target is TypeTarget.POLARS:
        from mountainash.core.lazy_imports import import_polars
        return import_polars().List(inner_native)
    if target is TypeTarget.NARWHALS:
        from mountainash.core.lazy_imports import import_narwhals
        return import_narwhals().List(inner_native)
    if target is TypeTarget.PYARROW:
        from mountainash.core.lazy_imports import import_pyarrow
        return import_pyarrow().list_(inner_native)
    if target is TypeTarget.IBIS:
        return f"array<{inner_native}>"  # ibis schema is string-keyed
    return bare_native  # PANDAS — no native parameterized list dtype


# ============================================================================
# Polars Converters
# ============================================================================

def to_polars_schema(schema: TypeSpec) -> Dict[str, Any]:
    """
    Convert TypeSpec to Polars schema dict.

    Args:
        schema: TypeSpec to convert

    Returns:
        Dict mapping column names to Polars DataType objects

    Raises:
        ImportError: If polars is not installed

    Example:
        >>> schema = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        >>> polars_schema = to_polars_schema(schema)
        >>> polars_schema
        {'id': Int64, 'name': Utf8}
    """
    from mountainash.core.lazy_imports import import_polars
    if import_polars() is None:
        raise ImportError("polars is required for to_polars_schema()")
    result = {}
    for name, field in schema.fields.items():
        result[name] = _resolve_field_native(field, TypeTarget.POLARS, field_name=name)
    return result
# ============================================================================
# Pandas Converters
# ============================================================================

def to_pandas_dtypes(schema: TypeSpec) -> Dict[str, Any]:
    """
    Convert TypeSpec to pandas dtypes dict.

    Non-categorical fields map to pandas dtype strings; a field with
    ``categories`` set maps to a real ``pd.CategoricalDtype`` instance
    (item 54, gap 3) — accepted directly by ``df.astype(...)``.

    Args:
        schema: TypeSpec to convert

    Returns:
        Dict mapping column names to pandas dtype strings (or
        pd.CategoricalDtype instances for categorical fields)

    Example:
        >>> schema = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        >>> pandas_dtypes = to_pandas_dtypes(schema)
        >>> pandas_dtypes
        {'id': 'Int64', 'name': 'string'}
    """
    result: Dict[str, Any] = {}
    for name, field in schema.fields.items():
        result[name] = _resolve_field_native(field, TypeTarget.PANDAS, field_name=name)
    return result

# ============================================================================
# PyArrow Converters
# ============================================================================

def to_arrow_schema(schema: TypeSpec) -> 'pa.Schema':
    """
    Convert TypeSpec to PyArrow Schema.

    Args:
        schema: TypeSpec to convert

    Returns:
        PyArrow Schema object

    Raises:
        ImportError: If pyarrow is not installed

    Example:
        >>> schema = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        >>> arrow_schema = to_arrow_schema(schema)
        >>> arrow_schema
        id: int64
        name: string
    """
    from mountainash.core.lazy_imports import import_pyarrow
    pa = import_pyarrow()
    if pa is None:
        raise ImportError("pyarrow is required for to_arrow_schema()")
    return pa.schema([
        pa.field(name, _resolve_field_native(field, TypeTarget.PYARROW, field_name=name))
        for name, field in schema.fields.items()
    ])

# ============================================================================
# Ibis Converters
# ============================================================================

def to_ibis_schema(schema: TypeSpec) -> Dict[str, str]:
    """
    Convert TypeSpec to Ibis schema dict.

    Ibis uses string-based type names for backend-agnostic operations.

    Args:
        schema: TypeSpec to convert

    Returns:
        Dict mapping column names to Ibis type strings

    Example:
        >>> schema = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        >>> ibis_schema = to_ibis_schema(schema)
        >>> ibis_schema
        {'id': 'int64', 'name': 'string'}
    """
    return {
        name: _resolve_field_native(field, TypeTarget.IBIS, field_name=name)
        for name, field in schema.fields.items()
    }


# ============================================================================
# Utility Functions
# ============================================================================

def convert_to_backend(schema: TypeSpec, backend: str) -> Any:
    """
    Convert TypeSpec to the specified backend format.

    Args:
        schema: TypeSpec to convert
        backend: Backend name ("polars", "pandas", "arrow"/"pyarrow", "ibis")

    Returns:
        Backend-specific schema format

    Raises:
        ValueError: If backend is unknown
        ImportError: If backend library is not installed

    Example:
        >>> schema = TypeSpec.from_simple_dict({"id": "integer"})
        >>> convert_to_backend(schema, "pandas")
        {'id': 'Int64'}
    """
    if backend == "polars":
        return to_polars_schema(schema)
    elif backend == "pandas":
        return to_pandas_dtypes(schema)
    elif backend in ("arrow", "pyarrow"):
        return to_arrow_schema(schema)
    elif backend == "ibis":
        return to_ibis_schema(schema)
    else:
        raise ValueError(
            f"Unknown backend: {backend}. "
            f"Supported: polars, pandas, arrow, pyarrow, ibis"
        )


__all__ = [
    # Individual converters
    "to_polars_schema",
    "to_pandas_dtypes",
    "to_arrow_schema",
    "to_ibis_schema",

    # Generic converter
    "convert_to_backend",

    # Field-aware resolution
    "resolve_field_canonical",
    "declared_fields",
    "declared_element",
    "_resolve_field_native",
    "_resolve_field_target",
]
