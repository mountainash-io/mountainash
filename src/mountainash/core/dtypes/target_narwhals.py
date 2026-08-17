# src/mountainash/core/dtypes/target_narwhals.py
"""Narwhals target mappings. Imported lazily."""
from __future__ import annotations

from typing import Any, Optional

import narwhals as nw

from .canonical import MountainashDtype as D
from .errors import UnknownDtypeError

SCHEMA_TYPES: dict[D, Any] = {
    D.BOOL: nw.Boolean, D.I8: nw.Int8, D.I16: nw.Int16, D.I32: nw.Int32,
    D.I64: nw.Int64, D.U8: nw.UInt8, D.U16: nw.UInt16, D.U32: nw.UInt32,
    D.U64: nw.UInt64, D.FP32: nw.Float32, D.FP64: nw.Float64,
    D.STRING: nw.String, D.BINARY: nw.Binary, D.DATE: nw.Date,
    D.TIME: nw.Time, D.TIMESTAMP: nw.Datetime, D.DURATION: nw.Duration,
    D.LIST: nw.List, D.STRUCT: nw.Struct,
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

_UNTYPED_NAMES = {"Unknown"}

_FROM_NATIVE: dict[str, D] = {
    "Boolean": D.BOOL, "Int8": D.I8, "Int16": D.I16, "Int32": D.I32,
    "Int64": D.I64, "UInt8": D.U8, "UInt16": D.U16, "UInt32": D.U32,
    "UInt64": D.U64, "Float32": D.FP32, "Float64": D.FP64,
    "String": D.STRING, "Categorical": D.STRING, "Enum": D.STRING,
    "Binary": D.BINARY, "Date": D.DATE, "Time": D.TIME,
    "Datetime": D.TIMESTAMP, "Duration": D.DURATION,
    "List": D.LIST, "Array": D.LIST, "Struct": D.STRUCT,
}


def _base_name(native: Any) -> str:
    # Same class-vs-instance handling as target_polars
    if isinstance(native, type):
        return native.__name__
    return str(native).split("(", 1)[0]


def from_native(native: Any) -> Optional[D]:
    name = _base_name(native)
    if name in _UNTYPED_NAMES:
        return None
    if name in _FROM_NATIVE:
        return _FROM_NATIVE[name]
    raise UnknownDtypeError(f"Unrecognized Narwhals dtype: {native!r}")


def parse_type_string(s: str) -> Optional[Any]:
    if "(" not in s:
        t = getattr(nw, s, None)
        return t if isinstance(t, type) else None          # NOT issubclass(t, nw.DataType) — no such class
    from ._paramstring import parse_constructor_repr
    namespace = {
        n: getattr(nw, n) for n in
        ("Datetime", "Duration", "Decimal", "List", "Array", "Int8", "Int16",
         "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "Float32",
         "Float64", "Boolean", "String", "Binary", "Date", "Time",
         "Categorical", "Enum")
    }
    result = parse_constructor_repr(s, namespace)
    # No nw.DataType base class exists to isinstance-check instances against;
    # the namespace is closed + AST-validated upstream, so any non-None
    # construction is a legitimate parameterized dtype (DTypeClass instances
    # are not `type`s — isinstance(None-check) is precisely `result is not None`).
    return result
