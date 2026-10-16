# src/mountainash/core/dtypes/target_polars.py
"""Polars target mappings. Imported lazily by DtypeRegistry."""
from __future__ import annotations

from typing import Any, Optional

import polars as pl

from .canonical import (
    ArrayDtype, DecimalDtype, DurationDtype, ListDtype, MountainashDtype as D,
    NativeDtype, SchemaTypeStatus, StructDtype, TimeDtype, TimestampDtype,
)
from .targets import TypeTarget
from .errors import UnknownDtypeError

SCHEMA_TYPES: dict[D, Any] = {
    D.BOOL: pl.Boolean, D.I8: pl.Int8, D.I16: pl.Int16, D.I32: pl.Int32,
    D.I64: pl.Int64, D.U8: pl.UInt8, D.U16: pl.UInt16, D.U32: pl.UInt32,
    D.U64: pl.UInt64, D.FP32: pl.Float32, D.FP64: pl.Float64,
    D.STRING: pl.String, D.BINARY: pl.Binary, D.DATE: pl.Date,
    D.TIME: pl.Time, D.TIMESTAMP: pl.Datetime, D.DURATION: pl.Duration,
    D.LIST: pl.List, D.STRUCT: pl.Struct,
    D.JSON: pl.String, D.XSD_DURATION: pl.String,
    D.XSD_YEAR: pl.String, D.XSD_YEARMONTH: pl.String,
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

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


def to_native_decimal(dtype: DecimalDtype) -> Any:
    return pl.Decimal(dtype.precision, dtype.scale)


def _family(native: Any) -> D | None:
    return _FROM_NATIVE.get(_base_name(native))


def _is_complete(native: Any) -> bool:
    if _base_name(native) == "Decimal":
        return getattr(native, "precision", None) is not None
    return _base_name(native) != "Unknown"


def from_native(native: Any) -> Any:
    name = _base_name(native)
    if name == "Unknown":
        return SchemaTypeStatus.UNKNOWN
    if name == "Time":
        return TimeDtype(precision=9)
    if isinstance(native, type):
        if name in {"Datetime", "Duration", "List", "Struct"}:
            return _FROM_NATIVE[name]
        if name == "Array":
            return ArrayDtype()
    elif name == "Datetime":
        return TimestampDtype(
            precision={"s": 0, "ms": 3, "us": 6, "ns": 9}[native.time_unit],
            timezone_aware=native.time_zone is not None,
            timezone=native.time_zone,
        )
    elif name == "Duration":
        return DurationDtype(unit=native.time_unit, semantics="fixed")
    elif name == "Decimal":
        precision, scale = native.precision, native.scale
        if precision is not None and scale is not None:
            try:
                return DecimalDtype(precision, scale)
            except UnknownDtypeError:
                pass  # A native decimal may exceed the portable cast domain.
    elif name == "List":
        return ListDtype(element=from_native(native.inner))
    elif name == "Array":
        leaf = native
        dimensions = []
        while isinstance(leaf, pl.Array):
            dimensions.append(leaf.size)
            leaf = leaf.inner
        return ArrayDtype(element=from_native(leaf), dimensions=tuple(dimensions))
    elif name == "Struct":
        return StructDtype(fields=tuple(
            (field.name, from_native(field.dtype)) for field in native.fields
        ))
    if name in {"Null", "Decimal", "Categorical", "Enum", "Object"}:
        return NativeDtype(value=native, target=TypeTarget.POLARS)
    if name in _FROM_NATIVE:
        return _FROM_NATIVE[name]
    if isinstance(native, pl.DataType) or (
        isinstance(native, type) and issubclass(native, pl.DataType)
    ):
        return NativeDtype(value=native, target=TypeTarget.POLARS)
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
