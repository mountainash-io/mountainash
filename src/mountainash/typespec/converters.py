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

from typing import TYPE_CHECKING, Any, Dict
import warnings

from mountainash.core.dtypes import (
    ArrayDtype,
    DecimalDtype,
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


def resolve_field_canonical(field: "FieldSpec") -> Any:
    """Resolve a FieldSpec's canonical dtype, with field-context (format)
    handling for the geospatial types that to_canonical() cannot resolve
    on its own.

    GEOPOINT's canonical shape depends on field.format: "default" is a
    lexical string, "array" is a two-element list, "object" is a struct.
    GEOJSON always maps to canonical JSON (itself a native string on every
    dtype target) regardless of format ("default" or "topojson" — both are
    JSON objects per the Frictionless spec).

    Every other UniversalType delegates to to_canonical(field.type)
    unchanged.
    """
    broad = _resolve_broad_field_canonical(field)
    return field.dtype if field.dtype is not None else broad


def _resolve_broad_field_canonical(field: "FieldSpec") -> Any:
    """Resolve authored broad semantics independently of precise refinements."""
    fmt = field.format
    if field.type is UniversalType.GEOPOINT:
        if not isinstance(fmt, str) or fmt not in _GEOPOINT_FORMAT_CANONICAL:
            raise InvalidGeospatialFormatError(
                field.name,
                UniversalType.GEOPOINT,
                fmt,
                sorted(_GEOPOINT_FORMAT_CANONICAL),
            )
        return _GEOPOINT_FORMAT_CANONICAL[fmt]
    if field.type is UniversalType.GEOJSON:
        if not isinstance(fmt, str) or fmt not in _GEOJSON_FORMATS:
            raise InvalidGeospatialFormatError(
                field.name,
                UniversalType.GEOJSON,
                fmt,
                sorted(_GEOJSON_FORMATS),
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
    source: Any = SchemaTypeStatus.UNKNOWN,
) -> Any:
    """Resolve one declaration, honoring whole-field native refinements."""
    declared = resolve_field_canonical(field)
    if declared is SchemaTypeStatus.UNKNOWN:
        declared = _resolve_broad_field_canonical(field)
    dtype_native = _field_dtype_native(field)
    if dtype_native is not None and not field.backend_type:
        if dtype_native.target is not target:
            raise DtypeMappingError(
                f"field {field.name!r}: native override belongs to {dtype_native.target}, not {target}"
            )
        return dtype_native
    override = field.backend_type
    if override is None or (isinstance(override, str) and not override):
        children = effective_child_fields(field)
        if isinstance(declared, StructDtype) and children:
            declared = replace(declared, fields=tuple(
                (child.name, _resolve_field_target(child, target, emit_warning=emit_warning) or SchemaTypeStatus.UNKNOWN)
                for child in children
            ))
        elif isinstance(declared, (ListDtype, ArrayDtype)) and children:
            declared = replace(declared, element=StructDtype(fields=tuple(
                (child.name, _resolve_field_target(child, target, emit_warning=emit_warning) or SchemaTypeStatus.UNKNOWN)
                for child in children
            )))
        return resolve_dtype_parameters(declared, source)
    if isinstance(override, NativeDtype):
        if override.target is not target:
            raise DtypeMappingError(
                f"field {field.name!r}: native override belongs to {override.target}, not {target}"
            )
        effective = override
    else:
        native = registry.parse_type_string(override, target)
        if native is None:
            raise InvalidBackendTypeError(field.name, override, target)
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
                f"field {field.name!r} on {target.value}: {reason} between "
                f"canonical {declared!r} and native override {effective.value!r}; native override wins",
                UserWarning, stacklevel=3,
            )
    return effective


def _portable_child_fields(field: "FieldSpec") -> tuple[tuple[str, Any], ...] | None:
    dtype = field.dtype
    if isinstance(dtype, StructDtype):
        if dtype.native is not None:
            return None
        return dtype.fields if isinstance(dtype.fields, tuple) else None
    element = dtype.element if isinstance(dtype, (ListDtype, ArrayDtype)) else None
    if isinstance(element, StructDtype):
        if element.native is not None:
            return None
        return element.fields if isinstance(element.fields, tuple) else None
    return None


def effective_child_fields(field: "FieldSpec") -> tuple["FieldSpec", ...]:
    """Return fresh child views in the effective portable parent order.

    Matching legacy fields contribute metadata and compatible UNKNOWN details
    by name. Complete parent shapes exclude unmatched legacy children.
    """
    if field.backend_type or _field_dtype_native(field) is not None:
        return ()
    selected = _portable_child_fields(field)
    legacy_fields = field.object_fields if field.type is UniversalType.OBJECT else field.item_object_fields
    legacy_fields = legacy_fields or ()
    if selected is None:
        element = field.dtype.element if isinstance(field.dtype, (ListDtype, ArrayDtype)) else None
        if (
            not isinstance(field.dtype, (StructDtype, ListDtype, ArrayDtype))
            or isinstance(field.dtype, StructDtype) and field.dtype.fields is SchemaTypeStatus.UNKNOWN
            or element is SchemaTypeStatus.UNKNOWN
            or isinstance(element, StructDtype) and element.fields is SchemaTypeStatus.UNKNOWN
        ):
            return tuple(replace(child) for child in legacy_fields)
        return ()
    legacy_by_name = {child.name: child for child in legacy_fields}
    from .spec import FieldSpec

    result: list[FieldSpec] = []
    for name, parent_dtype in selected:
        legacy = legacy_by_name.get(name)
        child_dtype = parent_dtype
        if isinstance(child_dtype, NativeDtype):
            result.append(
                FieldSpec(name=name, backend_type=child_dtype)
                if legacy is None else replace(legacy, name=name, dtype=None, backend_type=child_dtype)
            )
            continue
        if legacy is not None:
            legacy_dtype = resolve_field_canonical(legacy)
            if child_dtype is SchemaTypeStatus.UNKNOWN:
                child_dtype = (
                    legacy_dtype
                    if legacy_dtype is not None and not isinstance(legacy_dtype, SchemaTypeStatus)
                    else SchemaTypeStatus.UNKNOWN
                )
            elif isinstance(child_dtype, (TimestampDtype, TimeDtype, DurationDtype,
                                          ListDtype, ArrayDtype, StructDtype)):
                child_dtype = resolve_dtype_parameters(child_dtype, legacy_dtype)
        if legacy is None:
            result.append(FieldSpec(name=name, dtype=child_dtype))
        elif child_dtype is SchemaTypeStatus.UNKNOWN:
            result.append(replace(legacy, name=name, dtype=child_dtype))
        else:
            broad, _ = from_canonical(child_dtype)
            result.append(replace(
                legacy, name=name, type=broad, dtype=child_dtype,
                object_fields=legacy.object_fields if broad is UniversalType.OBJECT else None,
                item_object_fields=legacy.item_object_fields if broad is UniversalType.ARRAY else None,
                item_type=legacy.item_type if broad is UniversalType.LIST else None,
                delimiter=legacy.delimiter if broad is UniversalType.LIST else None,
            ))
    return tuple(result)



def _resolve_field_native(field: "FieldSpec", target: TypeTarget) -> Any:
    """Lower the effective target and enrich canonical container declarations."""
    canon = _resolve_field_target(field, target)
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
    native = registry.to_native_schema(canon, target)
    if canon is MountainashDtype.LIST and field.item_object_fields is not None:
        native = _resolve_list_object_inner(field.name, field.item_object_fields, target, native)
    elif canon is MountainashDtype.LIST and field.item_type:
        native = _resolve_list_inner(field.name, field.item_type, target, native)
    elif canon is MountainashDtype.STRUCT and field.object_fields:
        native = _resolve_struct_inner(field.name, field.object_fields, target, native)
    return native


def _resolve_struct_inner(
    field_name: str, object_fields: list["FieldSpec"], target: TypeTarget, bare_native: Any,
) -> Any:
    """Build a fully parameterized native struct dtype from nested FieldSpecs."""
    if target is TypeTarget.PANDAS:
        return bare_native
    inner_pairs = [(f.name, _resolve_field_native(f, target)) for f in object_fields]
    if target is TypeTarget.POLARS:
        from mountainash.core.lazy_imports import import_polars
        pl = import_polars()
        return pl.Struct({name: native for name, native in inner_pairs})
    if target is TypeTarget.NARWHALS:
        from mountainash.core.lazy_imports import import_narwhals
        nw = import_narwhals()
        return nw.Struct({name: native for name, native in inner_pairs})
    if target is TypeTarget.PYARROW:
        from mountainash.core.lazy_imports import import_pyarrow
        pa = import_pyarrow()
        return pa.struct([pa.field(name, native) for name, native in inner_pairs])
    if target is TypeTarget.IBIS:
        inner_str = ", ".join(f"{name}: {native}" for name, native in inner_pairs)
        return f"struct<{inner_str}>"
    return bare_native
def _resolve_list_object_inner(
    field_name: str,
    item_object_fields: list["FieldSpec"],
    target: TypeTarget,
    bare_native: Any,
) -> Any:
    """Parameterize a native list with its schema-proven struct item shape."""
    if target is TypeTarget.PANDAS:
        return bare_native
    struct_native = _resolve_struct_inner(
        field_name,
        item_object_fields,
        target,
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
    pl = import_polars()
    if pl is None:
        raise ImportError("polars is required for to_polars_schema()")
    result = {}
    for f in schema.fields:
        result[f.name] = _resolve_field_native(f, TypeTarget.POLARS)
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
    for f in schema.fields:
        result[f.name] = _resolve_field_native(f, TypeTarget.PANDAS)
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
    return pa.schema(
        [pa.field(f.name, _resolve_field_native(f, TypeTarget.PYARROW)) for f in schema.fields]
    )


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
    return {f.name: _resolve_field_native(f, TypeTarget.IBIS) for f in schema.fields}


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
]
