# src/mountainash/core/dtypes/target_pandas.py
"""pandas target mappings (string dtype names). Imported lazily."""
from __future__ import annotations

from typing import Any, Optional

from .canonical import MountainashDtype as D
from .errors import UnknownDtypeError

SCHEMA_TYPES: dict[D, str] = {
    D.BOOL: "boolean", D.I8: "Int8", D.I16: "Int16", D.I32: "Int32",
    D.I64: "Int64", D.U8: "UInt8", D.U16: "UInt16", D.U32: "UInt32",
    D.U64: "UInt64", D.FP32: "float32", D.FP64: "float64",
    D.STRING: "string", D.BINARY: "object", D.DATE: "datetime64[ns]",
    D.TIME: "object", D.TIMESTAMP: "datetime64[ns]",
    D.DURATION: "timedelta64[ns]", D.LIST: "object", D.STRUCT: "object",
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

_FROM_NATIVE: dict[str, D] = {
    "string": D.STRING, "str": D.STRING, "object": D.STRING,
    "category": D.STRING,
    "int8": D.I8, "int16": D.I16, "int32": D.I32, "int64": D.I64,
    "Int8": D.I8, "Int16": D.I16, "Int32": D.I32, "Int64": D.I64,
    "uint8": D.U8, "uint16": D.U16, "uint32": D.U32, "uint64": D.U64,
    "UInt8": D.U8, "UInt16": D.U16, "UInt32": D.U32, "UInt64": D.U64,
    "float16": D.FP32, "float32": D.FP32, "float64": D.FP64,
    "Float32": D.FP32, "Float64": D.FP64,
    "bool": D.BOOL, "boolean": D.BOOL,
    "datetime64": D.TIMESTAMP, "period": D.TIMESTAMP,
    "timedelta64": D.DURATION,
}


def _base_name(native: Any) -> str:
    # "datetime64[ns, UTC]" -> "datetime64"; "period[M]" -> "period"
    return str(native).split("[", 1)[0]


def from_native(native: Any) -> Optional[D]:
    name = _base_name(native)
    if name in _FROM_NATIVE:
        return _FROM_NATIVE[name]
    raise UnknownDtypeError(f"Unrecognized pandas dtype: {native!r}")


def parse_type_string(s: str) -> Optional[str]:
    try:
        import pandas as pd
        pd.api.types.pandas_dtype(s)
        return s
    except (ImportError, TypeError, ValueError):
        return None
