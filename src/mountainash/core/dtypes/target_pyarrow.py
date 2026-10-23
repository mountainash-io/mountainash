# src/mountainash/core/dtypes/target_pyarrow.py
"""PyArrow native type adapter and mapping tables. Imported lazily."""
from __future__ import annotations

import re
from dataclasses import is_dataclass, replace
from typing import Any, Callable, Optional

import pyarrow as pa

from ._lowering import lower_scalar, native_refinement, reject_bare_container_cast
from .canonical import (
    PARAMETERIZED_DTYPES, ArrayDtype, CastTarget, DecimalDtype, DurationDtype,
    ListDtype, MountainashDtype as D, NativeDtype, SchemaTypeStatus, StructDtype,
    TimeDtype, TimestampDtype, resolve_dtype_parameters,
)
from .errors import DtypeMappingError, UnknownDtypeError
from .protocols import NativeArrowTransportAdapter, NativeTypeAdapter, TypeEvidence
from .targets import TypeTarget

SCHEMA_TYPES: dict[D, Any] = {
    D.BOOL: pa.bool_(), D.I8: pa.int8(), D.I16: pa.int16(),
    D.I32: pa.int32(), D.I64: pa.int64(), D.U8: pa.uint8(),
    D.U16: pa.uint16(), D.U32: pa.uint32(), D.U64: pa.uint64(),
    D.FP32: pa.float32(), D.FP64: pa.float64(), D.STRING: pa.string(),
    D.BINARY: pa.binary(), D.DATE: pa.date32(), D.TIME: pa.time64("ns"),
    D.TIMESTAMP: pa.timestamp("ns"), D.DURATION: pa.duration("ns"),
    D.LIST: pa.list_(pa.string()), D.STRUCT: pa.struct([]),
    D.JSON: pa.string(), D.XSD_DURATION: pa.string(),
    D.XSD_YEAR: pa.string(), D.XSD_YEARMONTH: pa.string(),
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

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


def _family(native: Any) -> D | None:
    if isinstance(native, pa.Field):
        native = native.type
    return _FROM_NATIVE.get(_base_name(native))


def lower_parameterized(dtype: Any, lower_child: Callable[[Any], Any]) -> Any:
    """Construct the Arrow type of a parameterized portable dtype.

    ``lower_child`` supplies each nested child's Arrow type, so a caller may
    resolve children in its own domain (pandas ArrowDtype wrapping) or dispatch
    native children to their owners (transport).
    """
    if isinstance(dtype, TimestampDtype):
        precision = dtype.precision
        unit = "us" if precision is SchemaTypeStatus.UNKNOWN else {
            0: "s", 3: "ms", 6: "us", 9: "ns",
        }.get(precision)
        if unit is None:
            raise DtypeMappingError(f"PyArrow timestamp cannot represent precision {precision}")
        zone = dtype.timezone
        aware = dtype.timezone_aware is True or isinstance(zone, str)
        if aware and (zone is None or zone is SchemaTypeStatus.UNKNOWN):
            zone = "UTC"
        if not aware:
            zone = None
        return pa.timestamp(unit, tz=zone)
    if isinstance(dtype, TimeDtype):
        precision = 9 if dtype.precision is SchemaTypeStatus.UNKNOWN else dtype.precision
        unit = {0: "s", 3: "ms", 6: "us", 9: "ns"}.get(precision)
        if unit is None:
            raise DtypeMappingError(f"PyArrow time cannot represent precision {precision}")
        return pa.time32(unit) if unit in ("s", "ms") else pa.time64(unit)
    if isinstance(dtype, DurationDtype):
        if dtype.semantics == "calendar":
            unit = dtype.unit
            if unit is SchemaTypeStatus.UNKNOWN:
                raise DtypeMappingError("PyArrow calendar interval requires a known interval unit")
            if unit not in ("month_day_nano", "month_day_nano_interval"):
                raise DtypeMappingError(
                    f"PyArrow exposes only the combined month/day/nanosecond calendar interval; "
                    f"it cannot preserve unit {unit!r}"
                )
            return pa.month_day_nano_interval()
        unit = "us" if dtype.unit is SchemaTypeStatus.UNKNOWN else dtype.unit
        if unit not in ("s", "ms", "us", "ns"):
            raise DtypeMappingError(f"PyArrow fixed duration cannot represent unit {unit!r}")
        return pa.duration(unit)
    if isinstance(dtype, ListDtype):
        return pa.list_(pa.null() if dtype.element is SchemaTypeStatus.UNKNOWN else lower_child(dtype.element))
    if isinstance(dtype, ArrayDtype):
        if dtype.dimensions is SchemaTypeStatus.UNKNOWN:
            raise DtypeMappingError("PyArrow fixed-size list requires known dimensions")
        child = pa.null() if dtype.element is SchemaTypeStatus.UNKNOWN else lower_child(dtype.element)
        for size in reversed(dtype.dimensions):
            child = pa.list_(child, size)
        return child
    if isinstance(dtype, StructDtype):
        return pa.struct([] if dtype.fields is SchemaTypeStatus.UNKNOWN else [
            pa.field(name, pa.null() if child is SchemaTypeStatus.UNKNOWN else lower_child(child))
            for name, child in dtype.fields
        ])
    raise DtypeMappingError(f"Unsupported parameterized PyArrow dtype: {dtype!r}")


def to_arrow_portable(dtype: Any, lower_child: Callable[[Any], Any]) -> Any:
    """Arrow's construction of a portable dtype for native-to-Arrow transport.

    Scalars and parameterized leaves use Arrow's own construction; container
    children are lowered by ``lower_child`` so the transport entrypoint can
    dispatch native children to their owners. Parameters are not resolved
    here: transport receives the complete effective type.
    """
    if isinstance(dtype, DecimalDtype):
        return pa.decimal128(dtype.precision, dtype.scale)
    if isinstance(dtype, D):
        return lower_scalar(SCHEMA_TYPES, dtype, TypeTarget.PYARROW)
    return lower_parameterized(dtype, lower_child)


# Bounded bracket/paren family — the only parameterized forms PyArrow's
# str() emits that type_for_alias does not already parse.
_TIMESTAMP_RE = re.compile(r"^timestamp\[(\w+)(?:, tz=(.+))?\]$")
_DURATION_RE = re.compile(r"^duration\[(\w+)\]$")
_TIME_RE = re.compile(r"^time(32|64)\[(\w+)\]$")
_DECIMAL_RE = re.compile(r"^decimal(128|256)\((\d+),\s*(\d+)\)$")


class PyArrowTypeAdapter(
    NativeTypeAdapter["pa.DataType"],
    NativeArrowTransportAdapter["pa.DataType", "pa.DataType"],
):
    """Stateless Arrow lowering, decoding, parsing, equivalence and transport."""

    target = TypeTarget.PYARROW

    @staticmethod
    def _dtype_only(value: Any) -> Any:
        if isinstance(value, pa.Field):
            raise DtypeMappingError(
                "Arrow field qualifiers cannot be represented by a dtype-only schema mapping"
            )
        return value

    def to_native_schema(self, dtype: CastTarget) -> Any:
        native = native_refinement(dtype, self.target)
        if native is not None:
            return self._dtype_only(native.value)
        if isinstance(dtype, DecimalDtype):
            return pa.decimal128(dtype.precision, dtype.scale)
        if isinstance(dtype, PARAMETERIZED_DTYPES):
            return lower_parameterized(resolve_dtype_parameters(dtype), self.to_native_schema)
        return lower_scalar(SCHEMA_TYPES, dtype, self.target)

    def to_native_cast(self, dtype: CastTarget) -> Any:
        reject_bare_container_cast(dtype, self.target, SCHEMA_TYPES, CAST_UNSUPPORTED)
        return self.to_native_schema(dtype)

    def from_native(self, value: Any) -> TypeEvidence:
        """Retain portable parameters and native storage/field refinements."""
        if isinstance(value, pa.Field):
            decoded = self.from_native(value.type)
            if value.nullable and not value.metadata:
                return decoded
            evidence = NativeDtype(value=value.with_name(""), target=TypeTarget.PYARROW)
            return replace(decoded, native=evidence) if is_dataclass(decoded) else evidence
        if not isinstance(value, pa.DataType):
            raise UnknownDtypeError(f"Unrecognized PyArrow dtype: {value!r}")
        evidence = NativeDtype(value=value, target=TypeTarget.PYARROW)
        precision = {"s": 0, "ms": 3, "us": 6, "ns": 9}
        if pa.types.is_timestamp(value):
            return TimestampDtype(precision[value.unit], value.tz is not None, value.tz)
        if pa.types.is_time(value):
            return TimeDtype(precision[value.unit])
        if pa.types.is_duration(value):
            return DurationDtype(value.unit, "fixed")
        if pa.types.is_interval(value):
            return DurationDtype(unit=str(value), semantics="calendar", native=evidence)
        if pa.types.is_decimal(value):
            try:
                return DecimalDtype(
                    value.precision, value.scale,
                    native=evidence if value.bit_width != 128 else None,
                )
            except UnknownDtypeError:
                return evidence
        if pa.types.is_fixed_size_list(value):
            dimensions, leaf, qualified = [], value, False
            while pa.types.is_fixed_size_list(leaf):
                dimensions.append(leaf.list_size)
                field = leaf.value_field
                qualified |= bool(
                    field.metadata or not field.nullable or field.name not in ("item", "element")
                )
                leaf = leaf.value_type
            return ArrayDtype(
                self.from_native(leaf), tuple(dimensions), native=evidence if qualified else None,
            )
        if any(getattr(pa.types, kind, lambda _: False)(value) for kind in (
            "is_list", "is_large_list", "is_list_view", "is_large_list_view",
        )):
            field = value.value_field
            qualified = (
                not pa.types.is_list(value) or field.metadata or not field.nullable
                or field.name not in ("item", "element")
            )
            return ListDtype(self.from_native(field.type), native=evidence if qualified else None)
        if pa.types.is_struct(value):
            return StructDtype(
                tuple((field.name, self.from_native(field.type)) for field in value),
                native=evidence if any(field.metadata or not field.nullable for field in value) else None,
            )
        name = _base_name(value)
        if name in _FROM_NATIVE and name not in {
            "large_string", "large_utf8", "large_binary", "halffloat", "date64", "map",
        }:
            return _FROM_NATIVE[name]
        return evidence

    def parse_type_string(self, text: str) -> Optional[Any]:
        try:
            return pa.type_for_alias(text)  # unparameterized names, unchanged
        except (KeyError, ValueError):
            pass
        try:
            if m := _TIMESTAMP_RE.match(text):
                unit, tz = m.groups()
                return pa.timestamp(unit, tz=tz) if tz else pa.timestamp(unit)
            if m := _DURATION_RE.match(text):
                return pa.duration(m.group(1))
            if m := _TIME_RE.match(text):
                bits, unit = m.groups()
                return (pa.time32 if bits == "32" else pa.time64)(unit)
            if m := _DECIMAL_RE.match(text):
                bits, prec, scale = m.groups()
                ctor = pa.decimal128 if bits == "128" else pa.decimal256
                return ctor(int(prec), int(scale))
        except (KeyError, ValueError):
            # Syntactically-valid-but-semantically-invalid (timestamp[badunit],
            # decimal128(999, 10)) — return None so the resolver raises the typed
            # InvalidBackendTypeError instead of leaking a raw Arrow ValueError.
            return None
        return None

    def types_equal(self, left: Any, right: Any) -> bool:
        left_field, right_field = isinstance(left, pa.Field), isinstance(right, pa.Field)
        if left_field and right_field:
            # Nullability and metadata are qualifiers of the native evidence.
            return left.equals(right, check_metadata=True)
        if left_field or right_field:
            return False
        return left == right

    def to_arrow_transport(self, value: Any) -> Any:
        """Arrow's own dtype is its transport form; field qualifiers are refused.

        The registry also routes the absent-evidence state here: UNKNOWN carries
        no Arrow type, so its transport interpretation is the Arrow null type.
        """
        if value is SchemaTypeStatus.UNKNOWN:
            return pa.null()
        return self._dtype_only(value)
