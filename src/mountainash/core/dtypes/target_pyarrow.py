# src/mountainash/core/dtypes/target_pyarrow.py
"""PyArrow target mappings. Imported lazily."""
from __future__ import annotations

from typing import Any, Optional

import pyarrow as pa

from .canonical import MountainashDtype as D
from .errors import UnknownDtypeError

SCHEMA_TYPES: dict[D, Any] = {
    D.BOOL: pa.bool_(), D.I8: pa.int8(), D.I16: pa.int16(),
    D.I32: pa.int32(), D.I64: pa.int64(), D.U8: pa.uint8(),
    D.U16: pa.uint16(), D.U32: pa.uint32(), D.U64: pa.uint64(),
    D.FP32: pa.float32(), D.FP64: pa.float64(), D.STRING: pa.string(),
    D.BINARY: pa.binary(), D.DATE: pa.date32(), D.TIME: pa.time64("ns"),
    D.TIMESTAMP: pa.timestamp("ns"), D.DURATION: pa.duration("ns"),
    D.LIST: pa.list_(pa.string()), D.STRUCT: pa.struct([]),
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

_UNTYPED_NAMES = {"null"}

_FROM_NATIVE: dict[str, D] = {
    "string": D.STRING, "large_string": D.STRING, "utf8": D.STRING,
    "large_utf8": D.STRING,
    "int8": D.I8, "int16": D.I16, "int32": D.I32, "int64": D.I64,
    "uint8": D.U8, "uint16": D.U16, "uint32": D.U32, "uint64": D.U64,
    "halffloat": D.FP32, "float": D.FP32, "double": D.FP64,
    "bool": D.BOOL,
    "binary": D.BINARY, "large_binary": D.BINARY,
    "date32": D.DATE, "date64": D.DATE,
    "time32": D.TIME, "time64": D.TIME,
    "timestamp": D.TIMESTAMP, "duration": D.DURATION,
    "list": D.LIST, "large_list": D.LIST, "fixed_size_list": D.LIST,
    "struct": D.STRUCT, "map": D.STRUCT,
}


def _base_name(native: Any) -> str:
    # "timestamp[ns]" -> "timestamp"; "list<item: int64>" -> "list";
    # "date32[day]" -> "date32"
    return str(native).split("[", 1)[0].split("<", 1)[0]


def from_native(native: Any) -> Optional[D]:
    name = _base_name(native)
    if name in _UNTYPED_NAMES:
        return None
    if name in _FROM_NATIVE:
        return _FROM_NATIVE[name]
    raise UnknownDtypeError(f"Unrecognized PyArrow dtype: {native!r}")


def parse_type_string(s: str) -> Optional[Any]:
    try:
        return pa.type_for_alias(s)
    except (KeyError, ValueError):
        return None
