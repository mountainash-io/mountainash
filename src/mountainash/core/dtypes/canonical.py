# src/mountainash/core/dtypes/canonical.py
"""Canonical mountainash dtype vocabulary.

MountainashDtype is the ONLY in-memory type vocabulary. Substrait-aligned,
structural. UniversalType (Frictionless) lives at the TypeSpec boundary and
maps here via typespec.universal_types.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, ConfigDict

from .errors import UnknownDtypeError
from .targets import TypeTarget, detect_target


class MountainashDtype(str, Enum):
    """Canonical mountainash data type identifiers (Substrait-aligned)."""
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
    DURATION = "duration"
    LIST = "list"
    STRUCT = "struct"
    JSON = "json"
    XSD_DURATION = "xsd_duration"
    XSD_YEAR = "xsd_year"
    XSD_YEARMONTH = "xsd_yearmonth"


DTYPE_ALIASES: dict[str, MountainashDtype] = {
    # Canonical names (identity)
    **{m.value: m for m in MountainashDtype},
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
    "Duration": MountainashDtype.DURATION,
    "List": MountainashDtype.LIST,
    "Struct": MountainashDtype.STRUCT,
    # Python type names
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
    # Frictionless structural names (semantic year/yearmonth/any are NOT
    # aliases — they exist only in the boundary map)
    "integer": MountainashDtype.I64,
    "number": MountainashDtype.FP64,
    "datetime": MountainashDtype.TIMESTAMP,
    "array": MountainashDtype.LIST,
    "object": MountainashDtype.STRUCT,
}


_PYTHON_TYPE_MAP: dict[type, MountainashDtype] = {
    bool: MountainashDtype.BOOL,  # before int: bool subclasses int
    int: MountainashDtype.I64,
    float: MountainashDtype.FP64,
    str: MountainashDtype.STRING,
    bytes: MountainashDtype.BINARY,
}


def _datetime_type_map() -> dict[type, MountainashDtype]:
    import datetime
    return {
        datetime.datetime: MountainashDtype.TIMESTAMP,  # before date: datetime subclasses date
        datetime.date: MountainashDtype.DATE,
        datetime.time: MountainashDtype.TIME,
        datetime.timedelta: MountainashDtype.DURATION,
    }


class NativeDtype(BaseModel):
    """Explicit passthrough wrapper for a parameterized native dtype.

    Created by parse_cast_target when a user passes a native backend dtype
    (e.g. pl.Datetime("us", "UTC")) — never normalized to canon, so the
    parameters survive to compile time. Compiling on a backend other than
    `target` raises DtypeMappingError.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    value: Any
    target: TypeTarget


def parse_dtype(value: Any) -> MountainashDtype:
    """Normalize a canonical dtype specifier to the MountainashDtype enum.

    Accepts enum members, Python types (int/float/str/bool/bytes and the
    datetime types), and alias strings. Native backend dtype objects are NOT
    accepted — use parse_cast_target() (expression casts) or
    registry.from_native() (extraction).

    Raises:
        UnknownDtypeError: input is not a recognizable canonical dtype.
    """
    if isinstance(value, MountainashDtype):
        return value
    if isinstance(value, type):
        if value in _PYTHON_TYPE_MAP:
            return _PYTHON_TYPE_MAP[value]
        dt_map = _datetime_type_map()
        # datetime before date: see _datetime_type_map ordering
        for py_type, dtype in dt_map.items():
            if value is py_type:
                return dtype
    if isinstance(value, str):
        if value in DTYPE_ALIASES:
            return DTYPE_ALIASES[value]
        raise UnknownDtypeError(
            f"Unknown dtype string {value!r}. Use a canonical name like "
            f"'i64', 'string', 'fp64', or a MountainashDtype member."
        )
    if detect_target(value) is not None:
        raise UnknownDtypeError(
            f"{value!r} is a native backend dtype, not a canonical dtype. "
            f"Use parse_cast_target() for expression casts or "
            f"registry.from_native() for extraction."
        )
    raise UnknownDtypeError(
        f"Cannot interpret {value!r} (type {type(value).__name__}) as a dtype."
    )


def parse_cast_target(value: Any) -> Union[MountainashDtype, NativeDtype]:
    """Resolve a user-facing cast target.

    Canonical inputs normalize via parse_dtype. Native backend dtype objects
    wrap in NativeDtype WITHOUT normalization (parameters preserved).
    """
    try:
        return parse_dtype(value)
    except UnknownDtypeError:
        target = detect_target(value)
        if target is not None:
            return NativeDtype(value=value, target=target)
        raise
