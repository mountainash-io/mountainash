# src/mountainash/core/dtypes/target_polars.py
"""Polars target mappings. Imported lazily by DtypeRegistry."""
from __future__ import annotations

from typing import Any, Optional

import polars as pl

from .canonical import MountainashDtype as D
from .errors import UnknownDtypeError

SCHEMA_TYPES: dict[D, Any] = {
    D.BOOL: pl.Boolean, D.I8: pl.Int8, D.I16: pl.Int16, D.I32: pl.Int32,
    D.I64: pl.Int64, D.U8: pl.UInt8, D.U16: pl.UInt16, D.U32: pl.UInt32,
    D.U64: pl.UInt64, D.FP32: pl.Float32, D.FP64: pl.Float64,
    D.STRING: pl.String, D.BINARY: pl.Binary, D.DATE: pl.Date,
    D.TIME: pl.Time, D.TIMESTAMP: pl.Datetime, D.DURATION: pl.Duration,
    D.LIST: pl.List, D.STRUCT: pl.Struct,
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

# Explicitly untyped natives — from_native returns None (boundary renders ANY)
_UNTYPED_NAMES = {"Null", "Unknown"}

_FROM_NATIVE: dict[str, D] = {
    "Boolean": D.BOOL, "Int8": D.I8, "Int16": D.I16, "Int32": D.I32,
    "Int64": D.I64, "UInt8": D.U8, "UInt16": D.U16, "UInt32": D.U32,
    "UInt64": D.U64, "Float32": D.FP32, "Float64": D.FP64,
    "String": D.STRING, "Utf8": D.STRING, "Categorical": D.STRING,
    "Enum": D.STRING, "Binary": D.BINARY, "Date": D.DATE, "Time": D.TIME,
    "Datetime": D.TIMESTAMP, "Duration": D.DURATION,
    "List": D.LIST, "Array": D.LIST, "Struct": D.STRUCT,
}


def _base_name(native: Any) -> str:
    # Dtype CLASSES (pl.Int64 passed uninstantiated) -> __name__;
    # instances (pl.Datetime("us")) -> str() with params stripped.
    if isinstance(native, type):
        return native.__name__
    return str(native).split("(", 1)[0]


def from_native(native: Any) -> Optional[D]:
    name = _base_name(native)
    if name in _UNTYPED_NAMES:
        return None
    if name in _FROM_NATIVE:
        return _FROM_NATIVE[name]
    raise UnknownDtypeError(f"Unrecognized Polars dtype: {native!r}")


def parse_type_string(s: str) -> Optional[Any]:
    if "(" not in s:
        t = getattr(pl, s, None)
        return t if isinstance(t, type) and issubclass(t, pl.DataType) else None
    from ._paramstring import parse_constructor_repr
    namespace = {
        n: getattr(pl, n) for n in
        ("Datetime", "Duration", "Decimal", "List", "Array", "Int8", "Int16",
         "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "Float32",
         "Float64", "Boolean", "String", "Binary", "Date", "Time",
         "Categorical", "Enum")
    }
    result = parse_constructor_repr(s, namespace)
    if result is not None and isinstance(result, pl.DataType):
        return result
    return None
