# src/mountainash/core/dtypes/target_narwhals.py
"""Narwhals native type adapter and mapping tables. Imported lazily."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import narwhals as nw

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

SCHEMA_TYPES: dict[D, Any] = {
    D.BOOL: nw.Boolean, D.I8: nw.Int8, D.I16: nw.Int16, D.I32: nw.Int32,
    D.I64: nw.Int64, D.U8: nw.UInt8, D.U16: nw.UInt16, D.U32: nw.UInt32,
    D.U64: nw.UInt64, D.FP32: nw.Float32, D.FP64: nw.Float64,
    D.STRING: nw.String, D.BINARY: nw.Binary, D.DATE: nw.Date,
    D.TIME: nw.Time, D.TIMESTAMP: nw.Datetime, D.DURATION: nw.Duration,
    D.LIST: nw.List, D.STRUCT: nw.Struct,
    D.JSON: nw.String, D.XSD_DURATION: nw.String,
    D.XSD_YEAR: nw.String, D.XSD_YEARMONTH: nw.String,
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

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


def _family(native: Any) -> D | None:
    return _FROM_NATIVE.get(_base_name(native))


def _is_complete(native: Any) -> bool:
    if _base_name(native) == "Decimal":
        return getattr(native, "precision", None) is not None
    return _base_name(native) != "Unknown"


class NarwhalsTypeAdapter(
    NativeTypeAdapter[Any],
    NativeArrowTransportAdapter[Any, "pa.DataType"],
):
    """Stateless Narwhals lowering, decoding, parsing, equivalence and Arrow transport.

    Lowering constructs logical dtypes; execution support is separate.
    """

    target = TypeTarget.NARWHALS

    def to_native_schema(self, dtype: CastTarget) -> Any:
        native = native_refinement(dtype, self.target)
        if native is not None:
            return native.value
        if isinstance(dtype, DecimalDtype):
            return nw.Decimal(dtype.precision, dtype.scale)
        if isinstance(dtype, PARAMETERIZED_DTYPES):
            return self._lower_parameterized(resolve_dtype_parameters(dtype))
        return lower_scalar(SCHEMA_TYPES, dtype, self.target)

    def to_native_cast(self, dtype: CastTarget) -> Any:
        reject_bare_container_cast(dtype, self.target, SCHEMA_TYPES, CAST_UNSUPPORTED)
        return self.to_native_schema(dtype)

    def _lower_parameterized(self, dtype: Any) -> Any:
        unknown = SchemaTypeStatus.UNKNOWN
        if isinstance(dtype, TimestampDtype):
            unit = "us" if dtype.precision is unknown else {
                0: "s", 3: "ms", 6: "us", 9: "ns",
            }.get(dtype.precision)
            if unit is None:
                raise DtypeMappingError(
                    f"Narwhals Datetime cannot represent timestamp precision {dtype.precision}"
                )
            zone = dtype.timezone
            if dtype.timezone_aware is True and zone in (None, unknown):
                zone = "UTC"
            elif zone is unknown:
                zone = None
            return nw.Datetime(time_unit=unit, time_zone=zone)
        if isinstance(dtype, TimeDtype):
            if dtype.precision not in (unknown, 9):
                raise DtypeMappingError(
                    "Narwhals Time uses nanoseconds; other declared precisions are not representable"
                )
            return nw.Time
        if isinstance(dtype, DurationDtype):
            if dtype.semantics == "calendar":
                raise DtypeMappingError(
                    "Narwhals Duration cannot represent calendar duration semantics"
                )
            unit = "us" if dtype.unit is unknown else dtype.unit
            if unit not in {"s", "ms", "us", "ns"}:
                raise DtypeMappingError(
                    f"Narwhals Duration cannot represent unit {unit!r} exactly"
                )
            return nw.Duration(time_unit=unit)
        if isinstance(dtype, ListDtype):
            child = dtype.element
            return nw.List(nw.Unknown if child is unknown else self.to_native_schema(child))
        if isinstance(dtype, ArrayDtype):
            child = dtype.element
            native = nw.Unknown if child is unknown else self.to_native_schema(child)
            if dtype.dimensions is unknown:
                raise DtypeMappingError(
                    "Narwhals fixed arrays require known dimensions"
                )
            return nw.Array(native, shape=dtype.dimensions)
        if isinstance(dtype, StructDtype):
            fields = {} if dtype.fields is unknown else {
                name: nw.Unknown if child is unknown else self.to_native_schema(child)
                for name, child in dtype.fields
            }
            return nw.Struct(fields)
        raise TypeError(f"Unsupported parameterized Narwhals dtype: {dtype!r}")

    def from_native(self, value: Any) -> TypeEvidence:
        name = _base_name(value)
        if name == "Unknown":
            return SchemaTypeStatus.UNKNOWN
        if name == "Time":
            return TimeDtype()  # Narwhals Time does not expose native precision.
        if isinstance(value, type):
            if name in {"Datetime", "Duration", "List", "Struct"}:
                return _FROM_NATIVE[name]
            if name == "Array":
                return ArrayDtype()
        elif name == "Datetime":
            return TimestampDtype(
                precision={"s": 0, "ms": 3, "us": 6, "ns": 9}[value.time_unit],
                timezone_aware=value.time_zone is not None, timezone=value.time_zone,
            )
        elif name == "Duration":
            return DurationDtype(unit=value.time_unit, semantics="fixed")
        elif name == "Decimal":
            try:
                return DecimalDtype(value.precision, value.scale)
            except UnknownDtypeError:
                pass
        elif name == "List":
            return ListDtype(element=self.from_native(value.inner))
        elif name == "Array":
            leaf, dimensions = value, []
            while isinstance(leaf, nw.Array):
                dimensions.append(leaf.size)
                leaf = leaf.inner
            return ArrayDtype(element=self.from_native(leaf), dimensions=tuple(dimensions))
        elif name == "Struct":
            return StructDtype(fields=tuple(
                (field.name, self.from_native(field.dtype)) for field in value.fields
            ))
        if name in {"Decimal", "Categorical", "Enum", "Object"}:
            return NativeDtype(value=value, target=TypeTarget.NARWHALS)
        if name in _FROM_NATIVE:
            return _FROM_NATIVE[name]
        from narwhals.dtypes import DType
        if isinstance(value, DType) or isinstance(value, type) and issubclass(value, DType):
            return NativeDtype(value=value, target=TypeTarget.NARWHALS)
        raise UnknownDtypeError(f"Unrecognized Narwhals dtype: {value!r}")

    def parse_type_string(self, text: str) -> Optional[Any]:
        if "(" not in text:
            t = getattr(nw, text, None)
            return t if isinstance(t, type) else None          # NOT issubclass(t, nw.DataType) — no such class
        from ._paramstring import parse_constructor_repr
        namespace = {
            n: getattr(nw, n) for n in
            ("Datetime", "Duration", "Decimal", "List", "Array", "Int8", "Int16",
             "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64", "Float32",
             "Float64", "Boolean", "String", "Binary", "Date", "Time",
             "Categorical", "Enum")
        }
        # No nw.DataType base class exists to isinstance-check instances against;
        # the namespace is closed + AST-validated upstream, so any non-None
        # construction is a legitimate parameterized dtype.
        return parse_constructor_repr(text, namespace)

    def types_equal(self, left: Any, right: Any) -> bool:
        return left == right

    def to_arrow_transport(self, value: Any) -> "pa.DataType":
        from narwhals._arrow.utils import narwhals_to_native_dtype
        from narwhals._utils import Version
        return narwhals_to_native_dtype(value, Version.MAIN)
