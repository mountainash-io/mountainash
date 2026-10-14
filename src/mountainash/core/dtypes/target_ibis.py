# src/mountainash/core/dtypes/target_ibis.py
"""Ibis target mappings (string type names — ibis .cast() accepts them)."""
from __future__ import annotations

from typing import Any, Optional

from .canonical import (
    DecimalDtype, DurationDtype, ListDtype, MountainashDtype as D, NativeDtype,
    SchemaTypeStatus, StructDtype, TimeDtype, TimestampDtype,
)
from .targets import TypeTarget
from .errors import UnknownDtypeError

SCHEMA_TYPES: dict[D, str] = {
    D.BOOL: "boolean", D.I8: "int8", D.I16: "int16", D.I32: "int32",
    D.I64: "int64", D.U8: "uint8", D.U16: "uint16", D.U32: "uint32",
    D.U64: "uint64", D.FP32: "float32", D.FP64: "float64",
    D.STRING: "string", D.BINARY: "binary", D.DATE: "date",
    D.TIME: "time", D.TIMESTAMP: "timestamp", D.DURATION: "interval",
    D.LIST: "array", D.STRUCT: "struct",
    D.JSON: "string", D.XSD_DURATION: "string",
    D.XSD_YEAR: "string", D.XSD_YEARMONTH: "string",
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

_FROM_NATIVE: dict[str, D] = {
    "string": D.STRING,
    "int8": D.I8, "int16": D.I16, "int32": D.I32, "int64": D.I64,
    "uint8": D.U8, "uint16": D.U16, "uint32": D.U32, "uint64": D.U64,
    "float16": D.FP32, "float32": D.FP32, "float64": D.FP64,
    "bool": D.BOOL, "boolean": D.BOOL,
    "binary": D.BINARY, "date": D.DATE, "time": D.TIME,
    "timestamp": D.TIMESTAMP, "interval": D.DURATION,
    "array": D.LIST, "struct": D.STRUCT, "map": D.STRUCT,
}


def _base_name(native: Any) -> str:
    # "!int64" -> "int64"; "timestamp('UTC')" -> "timestamp";
    # "array<int64>" -> "array"
    s = str(native).lstrip("!")
    return s.split("(", 1)[0].split("<", 1)[0]


def to_native_decimal(dtype: DecimalDtype) -> Any:
    import ibis.expr.datatypes as dt
    return dt.Decimal(dtype.precision, dtype.scale)


def _family(native: Any) -> D | None:
    return _FROM_NATIVE.get(_base_name(native))


def _is_complete(native: Any) -> bool:
    return _base_name(native) != "decimal" or (
        getattr(native, "precision", None) is not None
        and getattr(native, "scale", None) is not None
    )


def from_native(native: Any) -> Any:
    import ibis.expr.datatypes as dt

    if isinstance(native, str):
        native = dt.dtype(native)
    if not isinstance(native, dt.DataType):
        raise UnknownDtypeError(f"Unrecognized Ibis dtype: {native!r}")
    name = _base_name(native)
    evidence = NativeDtype(value=native, target=TypeTarget.IBIS)
    refinement = evidence if not native.nullable else None
    if name == "timestamp":
        return TimestampDtype(
            precision=native.scale if native.scale is not None else SchemaTypeStatus.UNKNOWN,
            timezone_aware=native.timezone is not None,
            timezone=native.timezone, native=refinement,
        )
    if name == "time":
        return TimeDtype(native=refinement)
    if name == "interval":
        unit = native.unit.value
        return DurationDtype(
            unit=unit, semantics="calendar" if unit in {"Y", "Q", "M"} else "fixed",
            native=refinement,
        )
    if name == "array":
        return ListDtype(element=from_native(native.value_type), native=refinement)
    if name == "struct":
        return StructDtype(
            fields=tuple((key, from_native(value)) for key, value in native.fields.items()),
            native=refinement,
        )
    if name == "decimal":
        try:
            return DecimalDtype(native.precision, native.scale, native=refinement)
        except UnknownDtypeError:
            return evidence
    if name in _FROM_NATIVE and name not in {"float16", "map"}:
        return refinement if refinement is not None else _FROM_NATIVE[name]
    return evidence


def parse_type_string(s: str) -> Optional[str]:
    try:
        import ibis.expr.datatypes as dt
        dt.dtype(s)
        return s
    except Exception:
        return None
