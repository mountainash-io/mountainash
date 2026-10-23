# src/mountainash/core/dtypes/target_polars.py
"""Polars native type adapter and mapping tables. Imported lazily by DtypeRegistry."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import polars as pl

from ._lowering import lower_scalar, native_refinement, reject_bare_container_cast
from .canonical import (
    PARAMETERIZED_DTYPES, ArrayDtype, CastTarget, DecimalDtype, DurationDtype,
    ListDtype, MountainashDtype as D, NativeDtype, SchemaTypeStatus, StructDtype,
    TimeDtype, TimestampDtype, resolve_dtype_parameters,
)
from .errors import DtypeMappingError, UnknownDtypeError
from .protocols import NativeArrowTransportAdapter, NativeTypeAdapter, TypeEvidence
from .targets import TypeTarget

if TYPE_CHECKING:
    import pyarrow as pa

_TIME_UNITS = {3: "ms", 6: "us", 9: "ns"}


def _unit(precision: Any, family: str) -> str:
    if precision is SchemaTypeStatus.UNKNOWN:
        return "us"
    try:
        return _TIME_UNITS[precision]
    except KeyError:
        raise DtypeMappingError(
            f"Polars {family} cannot represent precision {precision}; "
            "supported precisions are 3, 6 and 9"
        ) from None


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


def _family(native: Any) -> D | None:
    return _FROM_NATIVE.get(_base_name(native))


def _is_complete(native: Any) -> bool:
    if _base_name(native) == "Decimal":
        return getattr(native, "precision", None) is not None
    return _base_name(native) != "Unknown"


class PolarsTypeAdapter(
    NativeTypeAdapter["pl.DataType | type[pl.DataType]"],
    NativeArrowTransportAdapter["pl.DataType | type[pl.DataType]", "pa.DataType"],
):
    """Stateless Polars lowering, decoding, parsing, equivalence and Arrow transport."""

    target = TypeTarget.POLARS

    def to_native_schema(self, dtype: CastTarget) -> Any:
        native = native_refinement(dtype, self.target)
        if native is not None:
            return native.value
        if isinstance(dtype, DecimalDtype):
            return pl.Decimal(dtype.precision, dtype.scale)
        if isinstance(dtype, PARAMETERIZED_DTYPES):
            return self._lower_parameterized(resolve_dtype_parameters(dtype))
        return lower_scalar(SCHEMA_TYPES, dtype, self.target)

    def to_native_cast(self, dtype: CastTarget) -> Any:
        reject_bare_container_cast(dtype, self.target, SCHEMA_TYPES, CAST_UNSUPPORTED)
        return self.to_native_schema(dtype)

    def _lower_parameterized(self, dtype: Any) -> Any:
        if isinstance(dtype, TimestampDtype):
            unit = _unit(dtype.precision, "timestamp")
            zone = dtype.timezone
            aware = dtype.timezone_aware is True or isinstance(zone, str)
            if aware and (zone is None or zone is SchemaTypeStatus.UNKNOWN):
                zone = "UTC"
            if not aware:
                zone = None
            return pl.Datetime(unit, zone)
        if isinstance(dtype, TimeDtype):
            if dtype.precision not in (SchemaTypeStatus.UNKNOWN, 9):
                raise DtypeMappingError(
                    f"Polars Time cannot represent precision {dtype.precision}; "
                    "supported precisions are UNKNOWN and 9"
                )
            return pl.Time
        if isinstance(dtype, DurationDtype):
            if dtype.semantics == "calendar":
                raise DtypeMappingError("Polars Duration represents fixed elapsed time, not calendar intervals")
            unit = dtype.unit
            if unit is SchemaTypeStatus.UNKNOWN:
                unit = "us"
            if unit not in ("ns", "us", "ms"):
                raise DtypeMappingError(f"Polars fixed Duration cannot represent unit {unit!r}")
            return pl.Duration(unit)
        if isinstance(dtype, ListDtype):
            inner = dtype.element
            return pl.List(pl.Null if inner is SchemaTypeStatus.UNKNOWN else self.to_native_schema(inner))
        if isinstance(dtype, ArrayDtype):
            if dtype.dimensions is SchemaTypeStatus.UNKNOWN:
                raise DtypeMappingError("Polars fixed Array requires known dimensions; it cannot be represented as a variable List")
            child = (
                pl.Null if dtype.element is SchemaTypeStatus.UNKNOWN
                else self.to_native_schema(dtype.element)
            )
            for size in reversed(dtype.dimensions):
                child = pl.Array(child, size)
            return child
        if isinstance(dtype, StructDtype):
            fields = [] if dtype.fields is SchemaTypeStatus.UNKNOWN else [
                pl.Field(name, pl.Null if child is SchemaTypeStatus.UNKNOWN else self.to_native_schema(child))
                for name, child in dtype.fields
            ]
            return pl.Struct(fields)
        raise DtypeMappingError(f"Unsupported parameterized Polars dtype: {dtype!r}")

    def from_native(self, value: Any) -> TypeEvidence:
        name = _base_name(value)
        if name == "Unknown":
            return SchemaTypeStatus.UNKNOWN
        if name == "Time":
            return TimeDtype(precision=9)
        if isinstance(value, type):
            if name in {"Datetime", "Duration", "List", "Struct"}:
                return _FROM_NATIVE[name]
            if name == "Array":
                return ArrayDtype()
        elif name == "Datetime":
            return TimestampDtype(
                precision={"s": 0, "ms": 3, "us": 6, "ns": 9}[value.time_unit],
                timezone_aware=value.time_zone is not None,
                timezone=value.time_zone,
            )
        elif name == "Duration":
            return DurationDtype(unit=value.time_unit, semantics="fixed")
        elif name == "Decimal":
            precision, scale = value.precision, value.scale
            if precision is not None and scale is not None:
                try:
                    return DecimalDtype(precision, scale)
                except UnknownDtypeError:
                    pass  # A native decimal may exceed the portable cast domain.
        elif name == "List":
            return ListDtype(element=self.from_native(value.inner))
        elif name == "Array":
            leaf = value
            dimensions = []
            while isinstance(leaf, pl.Array):
                dimensions.append(leaf.size)
                leaf = leaf.inner
            return ArrayDtype(element=self.from_native(leaf), dimensions=tuple(dimensions))
        elif name == "Struct":
            return StructDtype(fields=tuple(
                (field.name, self.from_native(field.dtype)) for field in value.fields
            ))
        if name in {"Null", "Decimal", "Categorical", "Enum", "Object"}:
            return NativeDtype(value=value, target=TypeTarget.POLARS)
        if name in _FROM_NATIVE:
            return _FROM_NATIVE[name]
        if isinstance(value, pl.DataType) or (
            isinstance(value, type) and issubclass(value, pl.DataType)
        ):
            return NativeDtype(value=value, target=TypeTarget.POLARS)
        raise UnknownDtypeError(f"Unrecognized Polars dtype: {value!r}")

    def parse_type_string(self, text: str) -> Optional[Any]:
        if "(" not in text:
            t = getattr(pl, text, None)
            return t if isinstance(t, type) and issubclass(t, pl.DataType) else None
        from ._paramstring import parse_constructor_repr
        namespace = {
            n: getattr(pl, n) for n in
            ("Datetime", "Duration", "Decimal", "List", "Array", "Int8", "Int16",
             "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "Float32",
             "Float64", "Boolean", "String", "Binary", "Date", "Time",
             "Categorical", "Enum")
        }
        result = parse_constructor_repr(text, namespace)
        if result is not None and isinstance(result, pl.DataType):
            return result
        return None

    def types_equal(self, left: Any, right: Any) -> bool:
        return left == right

    def to_arrow_transport(self, value: Any) -> "pa.DataType":
        # An owned empty series, never a source-frame probe.
        return pl.Series("", [], dtype=value).to_arrow().type
