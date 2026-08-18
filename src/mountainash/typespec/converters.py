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

from mountainash.core.dtypes import (
    InvalidBackendTypeError,
    MountainashDtype,
    TypeTarget,
    UnknownDtypeError,
    registry,
)
from mountainash.typespec.universal_types import to_canonical

if TYPE_CHECKING:
    from .spec import FieldSpec, TypeSpec
    import pyarrow as pa


# ============================================================================
# Shared resolution core
# ============================================================================

def _resolve_field_native(field: "FieldSpec", target: TypeTarget) -> Any:
    """Resolve categories, backend overrides, canonical types, and containers."""
    if field.categories is not None and target in (TypeTarget.POLARS, TypeTarget.PANDAS):
        from mountainash.typespec._categorical import categorical_values
        values = categorical_values(field.categories)
        if target is TypeTarget.POLARS:
            from mountainash.core.lazy_imports import import_polars
            pl = import_polars()
            return pl.Enum([str(v) for v in values]) if field.categories_ordered else pl.Categorical
        import pandas as pd
        return pd.CategoricalDtype(categories=values, ordered=bool(field.categories_ordered))
    if field.backend_type:
        parsed = registry.parse_type_string(field.backend_type, target)
        if parsed is not None:
            return parsed
        raise InvalidBackendTypeError(field.name, field.backend_type, target)
    canon = to_canonical(field.type)
    if canon is None:
        canon = MountainashDtype.STRING
    native = registry.to_native_schema(canon, target)
    if canon is MountainashDtype.LIST and field.item_type:
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
]
