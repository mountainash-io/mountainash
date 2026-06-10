# src/mountainash/core/dtypes/target_python.py
"""Python type-hint target mappings (dataclass/Pydantic extraction)."""
from __future__ import annotations

import datetime
from typing import Any, Optional

from .canonical import MountainashDtype as D
from .errors import UnknownDtypeError

SCHEMA_TYPES: dict[D, Any] = {
    D.BOOL: bool, D.I8: int, D.I16: int, D.I32: int, D.I64: int,
    D.U8: int, D.U16: int, D.U32: int, D.U64: int,
    D.FP32: float, D.FP64: float, D.STRING: str, D.BINARY: bytes,
    D.DATE: datetime.date, D.TIME: datetime.time,
    D.TIMESTAMP: datetime.datetime, D.DURATION: datetime.timedelta,
    D.LIST: list, D.STRUCT: dict,
}

CAST_UNSUPPORTED: frozenset[D] = frozenset()  # not an expression backend

_FROM_TYPE: dict[type, D] = {
    bool: D.BOOL,  # before int
    int: D.I64,
    float: D.FP64,
    str: D.STRING,
    bytes: D.BINARY,
    datetime.datetime: D.TIMESTAMP,  # before date: datetime subclasses date
    datetime.date: D.DATE,
    datetime.time: D.TIME,
    datetime.timedelta: D.DURATION,
    list: D.LIST,
    dict: D.STRUCT,
}

_FROM_NAME: dict[str, D] = {
    "str": D.STRING, "int": D.I64, "float": D.FP64, "bool": D.BOOL,
    "bytes": D.BINARY, "list": D.LIST, "dict": D.STRUCT,
    "List": D.LIST, "Dict": D.STRUCT,
    "date": D.DATE, "time": D.TIME, "datetime": D.TIMESTAMP,
    "timedelta": D.DURATION,
}

_UNTYPED_NAMES = {"Any"}


def from_native(native: Any) -> Optional[D]:
    if native is Any or (isinstance(native, str) and native in _UNTYPED_NAMES):
        return None
    if isinstance(native, type):
        for py_type, dtype in _FROM_TYPE.items():
            if native is py_type:
                return dtype
    origin = getattr(native, "__origin__", None)
    if origin is not None and origin in _FROM_TYPE:
        return _FROM_TYPE[origin]
    if isinstance(native, str) and native in _FROM_NAME:
        return _FROM_NAME[native]
    raise UnknownDtypeError(f"Unrecognized Python type hint: {native!r}")


def parse_type_string(s: str) -> Optional[Any]:
    return None  # backend_type strings are never Python hints
