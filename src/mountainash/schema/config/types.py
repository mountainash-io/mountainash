"""
Universal Type System for DataFrame Schema Transformations

Provides a centralized type mapping system based on Frictionless Table Schema
specification, enabling consistent type conversions across all supported
DataFrame backends (Polars, pandas, PyArrow, Ibis, Narwhals).

This module is the single source of truth for ALL type conversions in the
package. No other module should contain hardcoded type mappings.

Architecture:
- Universal types based on Frictionless Data standard
- Bidirectional mappings: Universal ↔ Backend-specific
- Python type mappings for dataclass/Pydantic extraction
- Safe cast detection to prevent data loss
"""
from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Dict, Set, Tuple, Optional, Any, Union

if TYPE_CHECKING:
    import polars as pl
    import pyarrow as pa


# ============================================================================
# Universal Type Enum (Based on Frictionless Table Schema)
# ============================================================================

class UniversalType(StrEnum):
    """
    Universal data types based on Frictionless Table Schema specification.

    These types provide a common vocabulary for describing data across all
    DataFrame backends and Python type systems.

    Reference: https://specs.frictionlessdata.io/table-schema/#types-and-formats
    """
    # Basic types
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"  # Floating point
    BOOLEAN = "boolean"

    # Temporal types
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    DURATION = "duration"
    YEAR = "year"
    YEARMONTH = "yearmonth"

    # Complex types
    ARRAY = "array"
    OBJECT = "object"

    # Special
    ANY = "any"


# ============================================================================
# Forward Type Mappings: Universal → Backend-Specific
# ============================================================================

def _get_universal_to_polars() -> Dict[str, Any]:
    """
    Map universal types to Polars DataType.

    Lazy import to avoid loading Polars unless needed.
    """
    from mountainash.core.lazy_imports import import_polars
    pl = import_polars()
    if pl is None:
        raise ImportError("polars is required for Polars type mappings")

    return {
        UniversalType.STRING: pl.Utf8,
        UniversalType.INTEGER: pl.Int64,
        UniversalType.NUMBER: pl.Float64,
        UniversalType.BOOLEAN: pl.Boolean,
        UniversalType.DATE: pl.Date,
        UniversalType.TIME: pl.Time,
        UniversalType.DATETIME: pl.Datetime,
        UniversalType.DURATION: pl.Duration,
        UniversalType.YEAR: pl.Int32,  # Represent year as Int32
        UniversalType.YEARMONTH: pl.Utf8,  # Represent as string (e.g., "2024-01")
        UniversalType.ARRAY: pl.List,
        UniversalType.OBJECT: pl.Struct,
        UniversalType.ANY: pl.Utf8,  # Fallback to string
    }


# Pandas type mappings (string-based, no import needed)
UNIVERSAL_TO_PANDAS: Dict[str, str] = {
    UniversalType.STRING: "string",  # Nullable string dtype
    UniversalType.INTEGER: "Int64",  # Nullable integer
    UniversalType.NUMBER: "float64",
    UniversalType.BOOLEAN: "boolean",  # Nullable boolean
    UniversalType.DATE: "datetime64[ns]",  # pandas has no separate date type
    UniversalType.TIME: "object",  # pandas has no native time type
    UniversalType.DATETIME: "datetime64[ns]",
    UniversalType.DURATION: "timedelta64[ns]",
    UniversalType.YEAR: "Int64",  # Represent year as integer
    UniversalType.YEARMONTH: "period[M]",  # Use period with month frequency
    UniversalType.ARRAY: "object",
    UniversalType.OBJECT: "object",
    UniversalType.ANY: "object",
}


def _get_universal_to_arrow() -> Dict[str, Any]:
    """
    Map universal types to PyArrow DataType.

    Lazy import to avoid loading PyArrow unless needed.
    """
    from mountainash.core.lazy_imports import import_pyarrow
    pa = import_pyarrow()
    if pa is None:
        raise ImportError("pyarrow is required for PyArrow type mappings")

    return {
        UniversalType.STRING: pa.string(),
        UniversalType.INTEGER: pa.int64(),
        UniversalType.NUMBER: pa.float64(),
        UniversalType.BOOLEAN: pa.bool_(),
        UniversalType.DATE: pa.date32(),
        UniversalType.TIME: pa.time64('ns'),
        UniversalType.DATETIME: pa.timestamp('ns'),
        UniversalType.DURATION: pa.duration('ns'),
        UniversalType.YEAR: pa.int32(),  # Represent year as int32
        UniversalType.YEARMONTH: pa.string(),  # Represent as string (e.g., "2024-01")
        UniversalType.ARRAY: pa.list_(pa.string()),  # Default to list of strings
        UniversalType.OBJECT: pa.struct([]),  # Empty struct as default
        UniversalType.ANY: pa.string(),
    }


# Ibis type mappings (string-based for backend-agnostic API)
UNIVERSAL_TO_IBIS: Dict[str, str] = {
    UniversalType.STRING: "string",
    UniversalType.INTEGER: "int64",
    UniversalType.NUMBER: "float64",
    UniversalType.BOOLEAN: "bool",
    UniversalType.DATE: "date",
    UniversalType.TIME: "time",
    UniversalType.DATETIME: "timestamp",
    UniversalType.DURATION: "interval",
    UniversalType.YEAR: "int64",  # Represent year as int64
    UniversalType.YEARMONTH: "string",  # Represent as string (e.g., "2024-01")
    UniversalType.ARRAY: "array",
    UniversalType.OBJECT: "struct",
    UniversalType.ANY: "string",
}


# ============================================================================
# Reverse Type Mappings: Backend-Specific → Universal
# ============================================================================

# Polars → Universal (string-based to avoid imports)
POLARS_TO_UNIVERSAL: Dict[str, str] = {
    # String types
    "Utf8": UniversalType.STRING,
    "String": UniversalType.STRING,  # Polars v1.0+ uses "String" instead of "Utf8"
    "Categorical": UniversalType.STRING,
    "Enum": UniversalType.STRING,

    # Integer types (all map to universal integer)
    "Int8": UniversalType.INTEGER,
    "Int16": UniversalType.INTEGER,
    "Int32": UniversalType.INTEGER,
    "Int64": UniversalType.INTEGER,
    "UInt8": UniversalType.INTEGER,
    "UInt16": UniversalType.INTEGER,
    "UInt32": UniversalType.INTEGER,
    "UInt64": UniversalType.INTEGER,

    # Float types
    "Float32": UniversalType.NUMBER,
    "Float64": UniversalType.NUMBER,

    # Boolean
    "Boolean": UniversalType.BOOLEAN,

    # Temporal types
    "Date": UniversalType.DATE,
    "Time": UniversalType.TIME,
    "Datetime": UniversalType.DATETIME,
    "Duration": UniversalType.DURATION,

    # Complex types
    "List": UniversalType.ARRAY,
    "Array": UniversalType.ARRAY,
    "Struct": UniversalType.OBJECT,

    # Special
    "Null": UniversalType.ANY,
    "Unknown": UniversalType.ANY,
}


# Pandas → Universal
PANDAS_TO_UNIVERSAL: Dict[str, str] = {
    # String types
    "string": UniversalType.STRING,
    "object": UniversalType.STRING,  # Default: treat object as string
    "category": UniversalType.STRING,

    # Integer types
    "int8": UniversalType.INTEGER,
    "int16": UniversalType.INTEGER,
    "int32": UniversalType.INTEGER,
    "int64": UniversalType.INTEGER,
    "Int8": UniversalType.INTEGER,  # Nullable
    "Int16": UniversalType.INTEGER,
    "Int32": UniversalType.INTEGER,
    "Int64": UniversalType.INTEGER,
    "uint8": UniversalType.INTEGER,
    "uint16": UniversalType.INTEGER,
    "uint32": UniversalType.INTEGER,
    "uint64": UniversalType.INTEGER,
    "UInt8": UniversalType.INTEGER,
    "UInt16": UniversalType.INTEGER,
    "UInt32": UniversalType.INTEGER,
    "UInt64": UniversalType.INTEGER,

    # Float types
    "float16": UniversalType.NUMBER,
    "float32": UniversalType.NUMBER,
    "float64": UniversalType.NUMBER,
    "Float32": UniversalType.NUMBER,
    "Float64": UniversalType.NUMBER,

    # Boolean
    "bool": UniversalType.BOOLEAN,
    "boolean": UniversalType.BOOLEAN,

    # Temporal types
    "datetime64": UniversalType.DATETIME,
    "datetime64[ns]": UniversalType.DATETIME,
    "datetime64[ms]": UniversalType.DATETIME,
    "datetime64[us]": UniversalType.DATETIME,
    "datetime64[s]": UniversalType.DATETIME,
    "timedelta64": UniversalType.DURATION,
    "timedelta64[ns]": UniversalType.DURATION,
    "period": UniversalType.DATETIME,
}


# PyArrow → Universal (string-based to avoid imports)
ARROW_TO_UNIVERSAL: Dict[str, str] = {
    # String types
    "string": UniversalType.STRING,
    "large_string": UniversalType.STRING,
    "utf8": UniversalType.STRING,
    "large_utf8": UniversalType.STRING,

    # Integer types
    "int8": UniversalType.INTEGER,
    "int16": UniversalType.INTEGER,
    "int32": UniversalType.INTEGER,
    "int64": UniversalType.INTEGER,
    "uint8": UniversalType.INTEGER,
    "uint16": UniversalType.INTEGER,
    "uint32": UniversalType.INTEGER,
    "uint64": UniversalType.INTEGER,

    # Float types
    "float": UniversalType.NUMBER,  # Alias for float64
    "double": UniversalType.NUMBER,  # Alias for float64
    "float16": UniversalType.NUMBER,
    "float32": UniversalType.NUMBER,
    "float64": UniversalType.NUMBER,

    # Boolean
    "bool": UniversalType.BOOLEAN,

    # Temporal types
    "date32": UniversalType.DATE,
    "date64": UniversalType.DATE,
    "time32": UniversalType.TIME,
    "time64": UniversalType.TIME,
    "timestamp": UniversalType.DATETIME,
    "duration": UniversalType.DURATION,

    # Complex types
    "list": UniversalType.ARRAY,
    "large_list": UniversalType.ARRAY,
    "fixed_size_list": UniversalType.ARRAY,
    "struct": UniversalType.OBJECT,
    "map": UniversalType.OBJECT,

    # Special
    "null": UniversalType.ANY,
}


# Ibis → Universal
IBIS_TO_UNIVERSAL: Dict[str, str] = {
    # String types
    "string": UniversalType.STRING,

    # Integer types
    "int8": UniversalType.INTEGER,
    "int16": UniversalType.INTEGER,
    "int32": UniversalType.INTEGER,
    "int64": UniversalType.INTEGER,
    "uint8": UniversalType.INTEGER,
    "uint16": UniversalType.INTEGER,
    "uint32": UniversalType.INTEGER,
    "uint64": UniversalType.INTEGER,

    # Float types
    "float16": UniversalType.NUMBER,
    "float32": UniversalType.NUMBER,
    "float64": UniversalType.NUMBER,

    # Boolean
    "bool": UniversalType.BOOLEAN,
    "boolean": UniversalType.BOOLEAN,

    # Temporal types
    "date": UniversalType.DATE,
    "time": UniversalType.TIME,
    "timestamp": UniversalType.DATETIME,
    "interval": UniversalType.DURATION,

    # Complex types
    "array": UniversalType.ARRAY,
    "struct": UniversalType.OBJECT,
}


# ============================================================================
# Python Type Mappings (for dataclass/Pydantic extraction)
# ============================================================================

PYTHON_TO_UNIVERSAL: Dict[Union[type, str], str] = {
    # Direct type objects
    str: UniversalType.STRING,
    int: UniversalType.INTEGER,
    float: UniversalType.NUMBER,
    bool: UniversalType.BOOLEAN,

    # String representations (for type hint inspection)
    "str": UniversalType.STRING,
    "int": UniversalType.INTEGER,
    "float": UniversalType.NUMBER,
    "bool": UniversalType.BOOLEAN,
    "list": UniversalType.ARRAY,
    "dict": UniversalType.OBJECT,
    "List": UniversalType.ARRAY,
    "Dict": UniversalType.OBJECT,

    # typing module types (string representations)
    "Any": UniversalType.ANY,
}


# Datetime module types (imported separately to avoid import at module level)
def _get_python_datetime_mappings() -> Dict[Any, str]:
    """Get Python datetime type mappings with lazy import."""
    import datetime
    return {
        datetime.date: UniversalType.DATE,
        datetime.time: UniversalType.TIME,
        datetime.datetime: UniversalType.DATETIME,
        datetime.timedelta: UniversalType.DURATION,
        "date": UniversalType.DATE,
        "time": UniversalType.TIME,
        "datetime": UniversalType.DATETIME,
        "timedelta": UniversalType.DURATION,
    }


# ============================================================================
# Safe Cast Detection
# ============================================================================

# Define known safe type casts (from_type, to_type)
SAFE_CASTS: Set[Tuple[str, str]] = {
    # Widening integer casts (no data loss)
    (UniversalType.INTEGER, UniversalType.NUMBER),  # int → float (safe for reasonable ranges)

    # String casts (always safe, might lose semantic meaning)
    (UniversalType.INTEGER, UniversalType.STRING),
    (UniversalType.NUMBER, UniversalType.STRING),
    (UniversalType.BOOLEAN, UniversalType.STRING),
    (UniversalType.DATE, UniversalType.STRING),
    (UniversalType.TIME, UniversalType.STRING),
    (UniversalType.DATETIME, UniversalType.STRING),
    (UniversalType.DURATION, UniversalType.STRING),

    # Temporal conversions
    (UniversalType.DATE, UniversalType.DATETIME),  # Date → datetime (adds time component)
    (UniversalType.DATETIME, UniversalType.DATE),  # Datetime → date (loses time, but safe pattern)

    # Boolean conversions
    (UniversalType.BOOLEAN, UniversalType.INTEGER),  # bool → int (0/1)
}


# Define known UNSAFE casts that may lose data
UNSAFE_CASTS: Set[Tuple[str, str]] = {
    # Narrowing numeric casts
    (UniversalType.NUMBER, UniversalType.INTEGER),  # float → int (loses decimal)

    # String parsing (may fail)
    (UniversalType.STRING, UniversalType.INTEGER),
    (UniversalType.STRING, UniversalType.NUMBER),
    (UniversalType.STRING, UniversalType.BOOLEAN),
    (UniversalType.STRING, UniversalType.DATE),
    (UniversalType.STRING, UniversalType.TIME),
    (UniversalType.STRING, UniversalType.DATETIME),
}


# ============================================================================
# Utility Functions
# ============================================================================

def normalize_type(
    type_value: Any,
    source_format: str = "universal"
) -> str:
    """
    Normalize a type to universal type string.

    Args:
        type_value: Type to normalize (can be string, type object, or backend type)
        source_format: Source format hint ("universal", "polars", "pandas", "arrow",
                      "ibis", "python")

    Returns:
        Universal type string (e.g., "string", "integer", "number")

    Raises:
        ValueError: If type cannot be normalized

    Examples:
        >>> normalize_type("Int64", "polars")
        'integer'
        >>> normalize_type(int, "python")
        'integer'
        >>> normalize_type("float64", "pandas")
        'number'
    """
    # If already a universal type, return as-is
    if isinstance(type_value, str) and type_value in UniversalType:
        return type_value

    # Convert type_value to string for lookup
    type_str = str(type_value)

    # Handle type objects (e.g., <class 'int'>)
    if isinstance(type_value, type):
        # Check Python type mappings
        if type_value in PYTHON_TO_UNIVERSAL:
            return PYTHON_TO_UNIVERSAL[type_value]

        # Try datetime types
        try:
            datetime_mappings = _get_python_datetime_mappings()
            if type_value in datetime_mappings:
                return datetime_mappings[type_value]
        except ImportError:
            pass

        # Fallback to __name__
        type_str = type_value.__name__

    # Handle typing generics (e.g., List[str], Dict[str, int])
    if hasattr(type_value, '__origin__'):
        origin = type_value.__origin__
        # Check if origin is a basic type we can map
        if origin in PYTHON_TO_UNIVERSAL:
            return PYTHON_TO_UNIVERSAL[origin]
        # Handle string representations
        origin_name = getattr(origin, '__name__', str(origin))
        if origin_name == 'list':
            return UniversalType.ARRAY
        elif origin_name == 'dict':
            return UniversalType.OBJECT

    # Select mapping based on source format
    mapping: Dict[str, str] = {}
    if source_format == "polars":
        mapping = POLARS_TO_UNIVERSAL
    elif source_format == "pandas":
        mapping = PANDAS_TO_UNIVERSAL
    elif source_format == "arrow" or source_format == "pyarrow":
        mapping = ARROW_TO_UNIVERSAL
    elif source_format == "ibis":
        mapping = IBIS_TO_UNIVERSAL
    elif source_format == "python":
        # Combine regular and datetime mappings
        mapping = PYTHON_TO_UNIVERSAL.copy()
        try:
            mapping.update(_get_python_datetime_mappings())
        except ImportError:
            pass
    elif source_format == "universal":
        # Already checked above, but handle edge case
        if type_str in UniversalType:
            return type_str

    # Try direct lookup
    if type_str in mapping:
        return mapping[type_str]

    # Try case-insensitive lookup
    type_str_lower = type_str.lower()
    for key, value in mapping.items():
        # Only try case-insensitive match for string keys
        if isinstance(key, str) and key.lower() == type_str_lower:
            return value

    # Handle special cases

    # PyArrow types might be objects
    if source_format in ("arrow", "pyarrow") and hasattr(type_value, '__class__'):
        class_name = type_value.__class__.__name__.lower()
        # Match patterns like "Int64Type" → "int64"
        for key in mapping:
            if class_name.startswith(key.lower()):
                return mapping[key]

    # Polars types might be class objects
    if source_format == "polars" and hasattr(type_value, '__name__'):
        polars_type_name = type_value.__name__
        if polars_type_name in mapping:
            return mapping[polars_type_name]

    # Pandas dtype objects
    if source_format == "pandas" and hasattr(type_value, 'name'):
        if type_value.name in mapping:
            return mapping[type_value.name]

    # Handle Polars types with parameters (e.g., "Datetime(time_unit='us', time_zone=None)")
    if source_format == "polars" and "(" in type_str:
        # Extract base type name before parentheses
        base_type = type_str.split("(")[0]
        if base_type in mapping:
            return mapping[base_type]

    # Unknown type - log warning and return ANY
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(
        f"Unknown type '{type_value}' (format: {source_format}), "
        f"defaulting to 'any'"
    )
    return UniversalType.ANY


def is_safe_cast(from_type: str, to_type: str) -> bool:
    """
    Check if a type cast is safe (no data loss).

    Args:
        from_type: Source universal type
        to_type: Target universal type

    Returns:
        True if cast is safe, False if cast may lose data

    Examples:
        >>> is_safe_cast("integer", "number")
        True
        >>> is_safe_cast("number", "integer")
        False
    """
    # Same type is always safe
    if from_type == to_type:
        return True

    # Check safe casts
    if (from_type, to_type) in SAFE_CASTS:
        return True

    # Check unsafe casts
    if (from_type, to_type) in UNSAFE_CASTS:
        return False

    # Unknown cast - assume unsafe to be conservative
    return False


def get_polars_type(universal_type: str) -> Any:
    """
    Get Polars DataType for a universal type.

    Args:
        universal_type: Universal type string

    Returns:
        Polars DataType object

    Raises:
        ImportError: If polars is not installed
        KeyError: If universal type is unknown
    """
    mapping = _get_universal_to_polars()
    return mapping[universal_type]


def get_arrow_type(universal_type: str) -> Any:
    """
    Get PyArrow DataType for a universal type.

    Args:
        universal_type: Universal type string

    Returns:
        PyArrow DataType object

    Raises:
        ImportError: If pyarrow is not installed
        KeyError: If universal type is unknown
    """
    mapping = _get_universal_to_arrow()
    return mapping[universal_type]


# ============================================================================
# Type Mapping Access Functions (for lazy loading)
# ============================================================================

def get_universal_to_backend_mapping(backend: str) -> Dict[str, Any]:
    """
    Get universal → backend type mapping for a specific backend.

    Args:
        backend: Backend name ("polars", "pandas", "arrow", "ibis")

    Returns:
        Dict mapping universal types to backend-specific types

    Raises:
        ValueError: If backend is unknown
        ImportError: If backend library is not installed
    """
    if backend == "polars":
        return _get_universal_to_polars()
    elif backend == "pandas":
        return UNIVERSAL_TO_PANDAS
    elif backend in ("arrow", "pyarrow"):
        return _get_universal_to_arrow()
    elif backend == "ibis":
        return UNIVERSAL_TO_IBIS
    else:
        raise ValueError(f"Unknown backend: {backend}")


def get_backend_to_universal_mapping(backend: str) -> Dict[str, str]:
    """
    Get backend → universal type mapping for a specific backend.

    Args:
        backend: Backend name ("polars", "pandas", "arrow", "ibis")

    Returns:
        Dict mapping backend-specific types to universal types

    Raises:
        ValueError: If backend is unknown
    """
    if backend == "polars":
        return POLARS_TO_UNIVERSAL
    elif backend == "pandas":
        return PANDAS_TO_UNIVERSAL
    elif backend in ("arrow", "pyarrow"):
        return ARROW_TO_UNIVERSAL
    elif backend == "ibis":
        return IBIS_TO_UNIVERSAL
    else:
        raise ValueError(f"Unknown backend: {backend}")


__all__ = [
    # Enum
    "UniversalType",

    # Forward mappings
    "UNIVERSAL_TO_PANDAS",
    "UNIVERSAL_TO_IBIS",

    # Reverse mappings
    "POLARS_TO_UNIVERSAL",
    "PANDAS_TO_UNIVERSAL",
    "ARROW_TO_UNIVERSAL",
    "IBIS_TO_UNIVERSAL",
    "PYTHON_TO_UNIVERSAL",

    # Safe casts
    "SAFE_CASTS",
    "UNSAFE_CASTS",

    # Utility functions
    "normalize_type",
    "is_safe_cast",
    "get_polars_type",
    "get_arrow_type",
    "get_universal_to_backend_mapping",
    "get_backend_to_universal_mapping",
]
