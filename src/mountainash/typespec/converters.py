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

from typing import TYPE_CHECKING, Any, Dict
import warnings

from mountainash.core.dtypes import (
    DecimalDtype,
    NativeDtype,
    InvalidBackendTypeError,
    MountainashDtype,
    TypeTarget,
    UnknownDtypeError,
    registry,
)
from mountainash.typespec.errors import InvalidGeospatialFormatError
from mountainash.core.dtypes.errors import DtypeMappingError
from mountainash.typespec.universal_types import UniversalType, to_canonical

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


def _resolve_field_target(
    field: "FieldSpec", target: TypeTarget, *, emit_warning: bool = True,
) -> MountainashDtype | DecimalDtype | NativeDtype | None:
    """Resolve a declaration once, honoring its explicit native override."""
    declared = resolve_field_canonical(field)
    override = field.backend_type
    if override is None or (isinstance(override, str) and not override):
        return declared
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
        semantic_or_parameterized = declared in (
            MountainashDtype.JSON, MountainashDtype.XSD_DURATION,
            MountainashDtype.XSD_YEAR, MountainashDtype.XSD_YEARMONTH,
            MountainashDtype.TIMESTAMP, MountainashDtype.DURATION,
            MountainashDtype.LIST, MountainashDtype.STRUCT,
        )
        equivalent = False
        if not semantic_or_parameterized:
            expected = registry.to_native_schema(declared, target)
            equivalent = _native_types_equal(expected, effective.value, target)
        if not equivalent:
            reason = "equivalence unverified" if semantic_or_parameterized else "dtype mismatch"
            warnings.warn(
                f"field {field.name!r} on {target.value}: {reason} between "
                f"canonical {declared!r} and native override {effective.value!r}; native override wins",
                UserWarning, stacklevel=3,
            )
    return effective



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
