# src/mountainash/core/dtypes/target_ibis.py
"""Ibis target mappings (string type names — ibis .cast() accepts them)."""
from __future__ import annotations

from typing import Any, Optional

from .canonical import (
    ArrayDtype, DecimalDtype, DurationDtype, ListDtype, MountainashDtype as D,
    NativeDtype, SchemaTypeStatus, StructDtype, TimeDtype, TimestampDtype,
)
from .targets import TypeTarget
from .errors import DtypeMappingError, UnknownDtypeError

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


def to_native_parameterized(dtype: Any) -> Any:
    """Construct an Ibis logical datatype while retaining declared parameters.

    This is logical type construction only; it does not assert physical
    fidelity for any SQL dialect.
    """
    import ibis.expr.datatypes as dt

    unknown = SchemaTypeStatus.UNKNOWN
    if isinstance(dtype, TimestampDtype):
        scale = None if dtype.precision is unknown else dtype.precision
        timezone = dtype.timezone
        if dtype.timezone_aware is True and timezone in (None, unknown):
            timezone = "UTC"
        elif timezone is unknown:
            timezone = None
        return dt.Timestamp(scale=scale, timezone=timezone)
    if isinstance(dtype, TimeDtype):
        if dtype.precision is not unknown:
            raise DtypeMappingError(
                f"Ibis Time cannot represent requested precision {dtype.precision}: "
                "its native Time type has no scale parameter"
            )
        return dt.Time()
    if isinstance(dtype, DurationDtype):
        unit = dtype.unit
        if unit is unknown:
            unit = "M" if dtype.semantics == "calendar" else "s"
        if dtype.semantics == "calendar" and unit not in {"Y", "Q", "M"}:
            raise DtypeMappingError(
                f"Ibis interval unit {unit!r} cannot represent calendar semantics"
            )
        if dtype.semantics == "fixed" and unit in {"Y", "Q", "M"}:
            raise DtypeMappingError(
                f"Ibis interval unit {unit!r} cannot represent fixed-duration semantics"
            )
        return dt.Interval(unit=unit)
    if isinstance(dtype, ListDtype):
        from .registry import registry
        child = dtype.element
        value_type = (dt.null if child is unknown
                      else registry.to_native_schema(child, TypeTarget.IBIS))
        return dt.Array(value_type)
    if isinstance(dtype, ArrayDtype):
        from .registry import registry
        child = dtype.element
        value_type = (dt.null if child is unknown
                      else registry.to_native_schema(child, TypeTarget.IBIS))
        if dtype.dimensions is SchemaTypeStatus.UNKNOWN:
            raise DtypeMappingError("Ibis fixed arrays require known dimensions")
        result = value_type
        for length in reversed(dtype.dimensions):
            result = dt.Array(result, length=length)
        return result
    if isinstance(dtype, StructDtype):
        from .registry import registry
        fields = () if dtype.fields is SchemaTypeStatus.UNKNOWN else dtype.fields
        return dt.Struct.from_tuples(
            (name, dt.null if child is unknown else
             registry.to_native_schema(child, TypeTarget.IBIS))
            for name, child in fields
        )
    raise TypeError(f"Unsupported parameterized Ibis dtype: {dtype!r}")





def _family(native: Any) -> D | None:
    return _FROM_NATIVE.get(_base_name(native))


def _is_complete(native: Any) -> bool:
    if isinstance(native, str):
        return True  # A retained physical SQL description, including unbounded NUMERIC.
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
        element = from_native(native.value_type)
        length = getattr(native, "length", None)
        if length is not None:
            dimensions = (length,)
            if isinstance(element, ArrayDtype) and element.native is None:
                dimensions += element.dimensions
                element = element.element
            return ArrayDtype(element=element, dimensions=dimensions, native=refinement)
        return ListDtype(element=element, native=refinement)
    if name == "string" and getattr(native, "length", None) is not None:
        return evidence
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


def parse_type_string(s: str) -> Optional[Any]:
    try:
        import ibis.expr.datatypes as dt
        return dt.dtype(s)
    except Exception:
        return None
