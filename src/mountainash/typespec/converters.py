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
import logging

from .spec import TypeSpec
from .universal_types import (
    get_polars_type,
    get_arrow_type,
    UNIVERSAL_TO_PANDAS,
    UNIVERSAL_TO_IBIS,
)

if TYPE_CHECKING:
    import pyarrow as pa

logger = logging.getLogger(__name__)


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

    for field in schema.fields:
        # Prefer backend_type if available (preserves original precision)
        if field.backend_type:
            try:
                # Try to get Polars type by name
                polars_type = getattr(pl, field.backend_type, None)
                if polars_type is not None:
                    result[field.name] = polars_type
                    continue
            except (AttributeError, TypeError):
                logger.debug(f"Could not use backend_type {field.backend_type}, falling back to universal type")

        # Fallback to universal type mapping
        try:
            polars_type = get_polars_type(field.type)
            result[field.name] = polars_type
        except KeyError:
            logger.warning(f"Unknown universal type '{field.type}' for field '{field.name}', using Utf8")
            result[field.name] = pl.Utf8

    return result


# ============================================================================
# Pandas Converters
# ============================================================================

def to_pandas_dtypes(schema: TypeSpec) -> Dict[str, str]:
    """
    Convert TypeSpec to pandas dtypes dict.

    Args:
        schema: TypeSpec to convert

    Returns:
        Dict mapping column names to pandas dtype strings

    Example:
        >>> schema = TypeSpec.from_simple_dict({"id": "integer", "name": "string"})
        >>> pandas_dtypes = to_pandas_dtypes(schema)
        >>> pandas_dtypes
        {'id': 'Int64', 'name': 'string'}
    """
    result = {}

    for field in schema.fields:
        # Prefer backend_type if available
        if field.backend_type:
            # Use backend type as-is for pandas (it's already a string)
            result[field.name] = field.backend_type
            continue

        # Fallback to universal type mapping
        try:
            pandas_dtype = UNIVERSAL_TO_PANDAS[field.type]
            result[field.name] = pandas_dtype
        except KeyError:
            logger.warning(f"Unknown universal type '{field.type}' for field '{field.name}', using 'object'")
            result[field.name] = "object"

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

    fields = []

    for field in schema.fields:
        # Prefer backend_type if available
        if field.backend_type:
            try:
                # Try to parse PyArrow type from string
                arrow_type = pa.type_for_alias(field.backend_type)
                fields.append(pa.field(field.name, arrow_type))
                continue
            except (KeyError, pa.ArrowInvalid):
                logger.debug(f"Could not use backend_type {field.backend_type}, falling back to universal type")

        # Fallback to universal type mapping
        try:
            arrow_type = get_arrow_type(field.type)
            fields.append(pa.field(field.name, arrow_type))
        except KeyError:
            logger.warning(f"Unknown universal type '{field.type}' for field '{field.name}', using string")
            fields.append(pa.field(field.name, pa.string()))

    return pa.schema(fields)


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
    result = {}

    for field in schema.fields:
        # Prefer backend_type if available (if it's an Ibis type)
        if field.backend_type:
            # Use backend type as-is
            result[field.name] = field.backend_type
            continue

        # Fallback to universal type mapping
        try:
            ibis_type = UNIVERSAL_TO_IBIS[field.type]
            result[field.name] = ibis_type
        except KeyError:
            logger.warning(f"Unknown universal type '{field.type}' for field '{field.name}', using 'string'")
            result[field.name] = "string"

    return result


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
