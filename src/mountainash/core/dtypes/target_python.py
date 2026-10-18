# src/mountainash/core/dtypes/target_python.py
"""Python type-hint target mappings (dataclass/Pydantic extraction)."""
from __future__ import annotations

import datetime
import decimal
from typing import Any, Optional, get_args, get_origin

from .canonical import (
    ArrayDtype, DecimalDtype, DurationDtype, ListDtype, MountainashDtype as D,
    SchemaTypeStatus, StructDtype, TimeDtype, TimestampDtype,
)
from .targets import TypeTarget
from .errors import DtypeMappingError, UnknownDtypeError


SCHEMA_TYPES: dict[D, Any] = {
    D.BOOL: bool, D.I8: int, D.I16: int, D.I32: int, D.I64: int,
    D.U8: int, D.U16: int, D.U32: int, D.U64: int,
    D.FP32: float, D.FP64: float, D.STRING: str, D.BINARY: bytes,
    D.DATE: datetime.date, D.TIME: datetime.time,
    D.TIMESTAMP: datetime.datetime, D.DURATION: datetime.timedelta,
    D.LIST: list, D.STRUCT: dict,
    D.JSON: str, D.XSD_DURATION: str,
    D.XSD_YEAR: str, D.XSD_YEARMONTH: str,
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


def to_native_decimal(dtype: DecimalDtype) -> Any:
    return decimal.Decimal


def to_native_parameterized(dtype: Any) -> Any:
    """Return faithful Python carrier hints; reject detail erased by Python types."""
    unknown = SchemaTypeStatus.UNKNOWN
    if isinstance(dtype, TimestampDtype):
        if dtype.precision is not unknown:
            raise DtypeMappingError(
                "Python datetime type hints cannot encode timestamp precision"
            )
        if dtype.timezone_aware is not unknown:
            raise DtypeMappingError(
                "Python datetime type hints cannot encode timestamp awareness"
            )
        if dtype.timezone is not unknown:
            raise DtypeMappingError(
                "Python datetime type hints cannot encode a timezone identifier"
            )
        return datetime.datetime
    if isinstance(dtype, TimeDtype):
        if dtype.precision is not unknown:
            raise DtypeMappingError("Python time type hints cannot encode precision")
        return datetime.time
    if isinstance(dtype, DurationDtype):
        if dtype.unit is not unknown or dtype.semantics is not unknown:
            raise DtypeMappingError(
                "Python timedelta type hints cannot encode duration unit or calendar semantics"
            )
        return datetime.timedelta
    if isinstance(dtype, ListDtype):
        from .registry import registry
        child = dtype.element
        return list if child is unknown else list[
            registry.to_native_schema(child, TypeTarget.PYTHON)
        ]
    if isinstance(dtype, ArrayDtype):
        raise DtypeMappingError(
            "Python sequence type hints cannot encode fixed-array dimensions"
        )
    if isinstance(dtype, StructDtype):
        if dtype.fields is SchemaTypeStatus.UNKNOWN:
            return dict
        raise DtypeMappingError(
            "Python dict type hints cannot encode an ordered named struct schema"
        )
    raise TypeError(f"Unsupported parameterized Python dtype: {dtype!r}")





def from_native(native: Any) -> Any:
    if native is Any or (isinstance(native, str) and native in _UNTYPED_NAMES):
        return None
    origin = get_origin(native)
    if origin is list:
        args = get_args(native)
        element = from_native(args[0]) if args else SchemaTypeStatus.UNKNOWN
        return ListDtype(
            element=SchemaTypeStatus.UNCONSTRAINED if element is None else element,
        )
    if isinstance(native, type):
        for py_type, dtype in _FROM_TYPE.items():
            if native is py_type:
                return dtype
    if origin is not None and origin in _FROM_TYPE:
        return _FROM_TYPE[origin]
    if isinstance(native, str) and native in _FROM_NAME:
        return _FROM_NAME[native]
    raise UnknownDtypeError(f"Unrecognized Python type hint: {native!r}")


def parse_type_string(s: str) -> Optional[Any]:
    return None  # backend_type strings are never Python hints
