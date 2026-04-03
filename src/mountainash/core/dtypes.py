"""Canonical mountainash data type definitions.

Provides the single source of truth for type string resolution across all backends.
Every backend dtype map and the API builder normalize through this module.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class MountainashDtype(str, Enum):
    """Canonical mountainash data type identifiers.

    Tier 1: Simple types guaranteed to work across all backends.
    Substrait-aligned naming where applicable, extended with unsigned ints.
    """
    BOOL = "bool"
    I8 = "i8"
    I16 = "i16"
    I32 = "i32"
    I64 = "i64"
    U8 = "u8"
    U16 = "u16"
    U32 = "u32"
    U64 = "u64"
    FP32 = "fp32"
    FP64 = "fp64"
    STRING = "string"
    BINARY = "binary"
    DATE = "date"
    TIME = "time"
    TIMESTAMP = "timestamp"


DTYPE_ALIASES: dict[str, MountainashDtype] = {
    # Canonical names (identity)
    "bool": MountainashDtype.BOOL,
    "i8": MountainashDtype.I8,
    "i16": MountainashDtype.I16,
    "i32": MountainashDtype.I32,
    "i64": MountainashDtype.I64,
    "u8": MountainashDtype.U8,
    "u16": MountainashDtype.U16,
    "u32": MountainashDtype.U32,
    "u64": MountainashDtype.U64,
    "fp32": MountainashDtype.FP32,
    "fp64": MountainashDtype.FP64,
    "string": MountainashDtype.STRING,
    "binary": MountainashDtype.BINARY,
    "date": MountainashDtype.DATE,
    "time": MountainashDtype.TIME,
    "timestamp": MountainashDtype.TIMESTAMP,
    # Substrait alternatives
    "boolean": MountainashDtype.BOOL,
    # Polars/Narwhals capitalized style
    "Boolean": MountainashDtype.BOOL,
    "Int8": MountainashDtype.I8,
    "Int16": MountainashDtype.I16,
    "Int32": MountainashDtype.I32,
    "Int64": MountainashDtype.I64,
    "UInt8": MountainashDtype.U8,
    "UInt16": MountainashDtype.U16,
    "UInt32": MountainashDtype.U32,
    "UInt64": MountainashDtype.U64,
    "Float32": MountainashDtype.FP32,
    "Float64": MountainashDtype.FP64,
    "Utf8": MountainashDtype.STRING,
    "String": MountainashDtype.STRING,
    "Binary": MountainashDtype.BINARY,
    "Date": MountainashDtype.DATE,
    "Time": MountainashDtype.TIME,
    "Datetime": MountainashDtype.TIMESTAMP,
    # Python type str() representations
    "int": MountainashDtype.I64,
    "float": MountainashDtype.FP64,
    "str": MountainashDtype.STRING,
    # Common lowercase aliases
    "int8": MountainashDtype.I8,
    "int16": MountainashDtype.I16,
    "int32": MountainashDtype.I32,
    "int64": MountainashDtype.I64,
    "uint8": MountainashDtype.U8,
    "uint16": MountainashDtype.U16,
    "uint32": MountainashDtype.U32,
    "uint64": MountainashDtype.U64,
    "float32": MountainashDtype.FP32,
    "float64": MountainashDtype.FP64,
    "f32": MountainashDtype.FP32,
    "f64": MountainashDtype.FP64,
}


_PYTHON_TYPE_MAP: dict[type, MountainashDtype] = {
    int: MountainashDtype.I64,
    float: MountainashDtype.FP64,
    str: MountainashDtype.STRING,
    bool: MountainashDtype.BOOL,
}


def resolve_dtype(dtype: Any) -> str:
    """Resolve any dtype specifier to a canonical mountainash type string.

    Accepts:
      - MountainashDtype enum members
      - Python built-in types (int, float, str, bool)
      - Canonical strings ("i64", "string", etc.)
      - Alias strings ("Int64", "Utf8", "int64", etc.)
      - Native backend types (pl.Int64, nw.String, ibis dt) via str() conversion

    Returns:
      Canonical type string (e.g., "i64", "string", "fp64").

    Raises:
      ValueError: If dtype cannot be resolved to a known type.
    """
    if isinstance(dtype, MountainashDtype):
        return dtype.value

    # Check bool before int — bool is a subclass of int in Python
    if isinstance(dtype, type) and dtype in _PYTHON_TYPE_MAP:
        return _PYTHON_TYPE_MAP[dtype].value

    dtype_str = str(dtype)

    if dtype_str in DTYPE_ALIASES:
        return DTYPE_ALIASES[dtype_str].value

    raise ValueError(
        f"Unknown dtype: {dtype!r} (resolved to string {dtype_str!r}). "
        f"Use a canonical type like 'i64', 'string', 'fp64', or a MountainashDtype enum."
    )
