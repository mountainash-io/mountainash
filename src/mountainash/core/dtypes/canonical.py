# src/mountainash/core/dtypes/canonical.py
"""Canonical mountainash dtype vocabulary.

MountainashDtype is the ONLY in-memory type vocabulary. Substrait-aligned,
structural. UniversalType (Frictionless) lives at the TypeSpec boundary and
maps here via typespec.universal_types.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, ConfigDict

from .errors import UnknownDtypeError
from .targets import TypeTarget, detect_target

class SchemaTypeStatus(Enum):
    """Non-type states in an inferred schema."""

    UNKNOWN = "unknown"
    UNCONSTRAINED = "unconstrained"


class MountainashDtype(str, Enum):
    """Canonical mountainash data type identifiers (Substrait-aligned)."""
    BOOL = "bool"
    I8 = "i8"
    I16 = "i16"
    I32 = "i32"
    I64 = "i64"
    U8 = "u8"
    U16 = "u16"
    U32 = "u32"
    U64 = "u64"
    FP32 = "fp32"
    FP64 = "fp64"
    STRING = "string"
    BINARY = "binary"
    DATE = "date"
    TIME = "time"
    TIMESTAMP = "timestamp"
    DURATION = "duration"
    LIST = "list"
    STRUCT = "struct"
    JSON = "json"
    XSD_DURATION = "xsd_duration"
    XSD_YEAR = "xsd_year"
    XSD_YEARMONTH = "xsd_yearmonth"


DTYPE_ALIASES: dict[str, MountainashDtype] = {
    # Canonical names (identity)
    **{m.value: m for m in MountainashDtype},
    # Substrait alternatives
    "boolean": MountainashDtype.BOOL,
    # Polars/Narwhals capitalized style
    "Boolean": MountainashDtype.BOOL,
    "Int8": MountainashDtype.I8,
    "Int16": MountainashDtype.I16,
    "Int32": MountainashDtype.I32,
    "Int64": MountainashDtype.I64,
    "UInt8": MountainashDtype.U8,
    "UInt16": MountainashDtype.U16,
    "UInt32": MountainashDtype.U32,
    "UInt64": MountainashDtype.U64,
    "Float32": MountainashDtype.FP32,
    "Float64": MountainashDtype.FP64,
    "Utf8": MountainashDtype.STRING,
    "String": MountainashDtype.STRING,
    "Binary": MountainashDtype.BINARY,
    "Date": MountainashDtype.DATE,
    "Time": MountainashDtype.TIME,
    "Datetime": MountainashDtype.TIMESTAMP,
    "Duration": MountainashDtype.DURATION,
    "List": MountainashDtype.LIST,
    "Struct": MountainashDtype.STRUCT,
    # Python type names
    "int": MountainashDtype.I64,
    "float": MountainashDtype.FP64,
    "str": MountainashDtype.STRING,
    # Common lowercase aliases
    "int8": MountainashDtype.I8,
    "int16": MountainashDtype.I16,
    "int32": MountainashDtype.I32,
    "int64": MountainashDtype.I64,
    "uint8": MountainashDtype.U8,
    "uint16": MountainashDtype.U16,
    "uint32": MountainashDtype.U32,
    "uint64": MountainashDtype.U64,
    "float32": MountainashDtype.FP32,
    "float64": MountainashDtype.FP64,
    "f32": MountainashDtype.FP32,
    "f64": MountainashDtype.FP64,
    # Frictionless structural names (semantic year/yearmonth/any are NOT
    # aliases — they exist only in the boundary map)
    "integer": MountainashDtype.I64,
    "number": MountainashDtype.FP64,
    "datetime": MountainashDtype.TIMESTAMP,
    "array": MountainashDtype.LIST,
    "object": MountainashDtype.STRUCT,
}


_PYTHON_TYPE_MAP: dict[type, MountainashDtype] = {
    bool: MountainashDtype.BOOL,  # before int: bool subclasses int
    int: MountainashDtype.I64,
    float: MountainashDtype.FP64,
    str: MountainashDtype.STRING,
    bytes: MountainashDtype.BINARY,
}


def _datetime_type_map() -> dict[type, MountainashDtype]:
    import datetime
    return {
        datetime.datetime: MountainashDtype.TIMESTAMP,  # before date: datetime subclasses date
        datetime.date: MountainashDtype.DATE,
        datetime.time: MountainashDtype.TIME,
        datetime.timedelta: MountainashDtype.DURATION,
    }


class NativeDtype(BaseModel):
    """Explicit passthrough wrapper for a parameterized native dtype.

    Created by parse_cast_target when a user passes a native backend dtype
    (e.g. pl.Datetime("us", "UTC")) — never normalized to canon, so the
    parameters survive to compile time. Compiling on a backend other than
    `target` raises DtypeMappingError.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    value: Any
    target: TypeTarget


@dataclass(frozen=True)
class TimestampDtype:
    precision: int | SchemaTypeStatus = SchemaTypeStatus.UNKNOWN
    timezone_aware: bool | SchemaTypeStatus = SchemaTypeStatus.UNKNOWN
    timezone: str | None | SchemaTypeStatus = SchemaTypeStatus.UNKNOWN
    native: NativeDtype | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if isinstance(self.precision, bool) or (
            not isinstance(self.precision, int)
            and self.precision is not SchemaTypeStatus.UNKNOWN
        ):
            raise UnknownDtypeError("Timestamp precision must be a non-negative integer or UNKNOWN")
        if isinstance(self.precision, int) and self.precision < 0:
            raise UnknownDtypeError("Timestamp precision must be non-negative")
        if self.timezone_aware is False and isinstance(self.timezone, str):
            raise UnknownDtypeError("A naive timestamp cannot have a named timezone")
        if not (
            self.timezone_aware is True or self.timezone_aware is False
            or self.timezone_aware is SchemaTypeStatus.UNKNOWN
        ):
            raise UnknownDtypeError("Timestamp awareness must be bool or UNKNOWN")
        if not (
            self.timezone is None or isinstance(self.timezone, str)
            or self.timezone is SchemaTypeStatus.UNKNOWN
        ):
            raise UnknownDtypeError("Timestamp timezone must be a string, None or UNKNOWN")


@dataclass(frozen=True)
class TimeDtype:
    precision: int | SchemaTypeStatus = SchemaTypeStatus.UNKNOWN
    native: NativeDtype | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if self.precision is not SchemaTypeStatus.UNKNOWN and (
            isinstance(self.precision, bool) or not isinstance(self.precision, int)
            or self.precision < 0
        ):
            raise UnknownDtypeError("Time precision must be a non-negative integer or UNKNOWN")


@dataclass(frozen=True)
class DurationDtype:
    unit: str | SchemaTypeStatus = SchemaTypeStatus.UNKNOWN
    semantics: str | SchemaTypeStatus = SchemaTypeStatus.UNKNOWN
    native: NativeDtype | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if self.semantics not in (SchemaTypeStatus.UNKNOWN, "fixed", "calendar"):
            raise UnknownDtypeError(f"Invalid duration semantics: {self.semantics!r}")
        if self.unit is not SchemaTypeStatus.UNKNOWN and (
            not isinstance(self.unit, str) or not self.unit
        ):
            raise UnknownDtypeError("Duration unit must be a nonempty string or UNKNOWN")


@dataclass(frozen=True)
class ListDtype:
    element: Any = SchemaTypeStatus.UNKNOWN
    native: NativeDtype | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class ArrayDtype:
    element: Any = SchemaTypeStatus.UNKNOWN
    dimensions: tuple[int, ...] | SchemaTypeStatus = SchemaTypeStatus.UNKNOWN
    native: NativeDtype | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if self.dimensions is not SchemaTypeStatus.UNKNOWN and (
            not isinstance(self.dimensions, tuple) or not self.dimensions
            or any(isinstance(size, bool) or not isinstance(size, int) or size < 0
                   for size in self.dimensions)
        ):
            raise UnknownDtypeError("Array dimensions must be a nonempty tuple of non-negative integers or UNKNOWN")


@dataclass(frozen=True)
class StructDtype:
    fields: tuple[tuple[str, Any], ...] | SchemaTypeStatus = SchemaTypeStatus.UNKNOWN
    native: NativeDtype | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if self.fields is not SchemaTypeStatus.UNKNOWN and (
            not isinstance(self.fields, tuple)
            or any(not isinstance(pair, tuple) or len(pair) != 2
                   or not isinstance(pair[0], str) for pair in self.fields)
        ):
            raise UnknownDtypeError("Struct fields must be an ordered tuple of (name, dtype) pairs or UNKNOWN")


@dataclass(frozen=True)
class DecimalDtype:
    """Portable exact decimal: precision = total digits, scale = fractional digits."""
    precision: int
    scale: int
    native: NativeDtype | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        p, s = self.precision, self.scale
        if (
            isinstance(p, bool) or isinstance(s, bool)
            or not isinstance(p, int) or not isinstance(s, int)
        ):
            raise UnknownDtypeError(
                f"DecimalDtype precision/scale must be int, got {p!r}, {s!r}"
            )
        if not 1 <= p <= 38 or not 0 <= s <= p:
            raise UnknownDtypeError(
                "DecimalDtype requires 1 <= precision <= 38 and "
                f"0 <= scale <= precision, got ({p}, {s})"
            )

    def __str__(self) -> str:
        return f"decimal({self.precision},{self.scale})"


def dtype_family(value: Any) -> Any:
    """Classify a dtype without treating the result as a cast target."""
    if isinstance(value, DecimalDtype):
        return value
    if isinstance(value, TimestampDtype):
        return MountainashDtype.TIMESTAMP
    if isinstance(value, TimeDtype):
        return MountainashDtype.TIME
    if isinstance(value, DurationDtype):
        return MountainashDtype.DURATION
    if isinstance(value, (ListDtype, ArrayDtype)):
        return MountainashDtype.LIST
    if isinstance(value, StructDtype):
        return MountainashDtype.STRUCT
    if isinstance(value, NativeDtype):
        from .registry import registry
        classify = getattr(registry._target(value.target), "_family", None)
        family = classify(value.value) if classify is not None else None
        return family if family is not None else value
    return value


def dtype_is_complete(value: Any) -> bool:
    """Whether the descriptor establishes every required type parameter."""
    if isinstance(value, SchemaTypeStatus):
        return False
    if isinstance(value, MountainashDtype):
        return value not in {
            MountainashDtype.TIMESTAMP, MountainashDtype.TIME, MountainashDtype.DURATION,
            MountainashDtype.LIST, MountainashDtype.STRUCT,
        }
    if isinstance(value, NativeDtype):
        from .registry import registry
        check = getattr(registry._target(value.target), "_is_complete", None)
        return check(value.value) if check is not None else True
    if isinstance(value, DecimalDtype):
        return True
    if isinstance(value, TimestampDtype):
        return all(v is not SchemaTypeStatus.UNKNOWN for v in (
            value.precision, value.timezone_aware, value.timezone
        ))
    if isinstance(value, TimeDtype):
        return value.precision is not SchemaTypeStatus.UNKNOWN
    if isinstance(value, DurationDtype):
        return value.unit is not SchemaTypeStatus.UNKNOWN and value.semantics is not SchemaTypeStatus.UNKNOWN
    if isinstance(value, ListDtype):
        return dtype_is_complete(value.element)
    if isinstance(value, ArrayDtype):
        return dtype_is_complete(value.element) and value.dimensions is not SchemaTypeStatus.UNKNOWN
    if isinstance(value, StructDtype):
        return value.fields is not SchemaTypeStatus.UNKNOWN and all(
            dtype_is_complete(t) for _, t in value.fields
        )
    return False

def parse_dtype(value: Any) -> MountainashDtype:
    """Normalize a canonical dtype specifier to the MountainashDtype enum.

    Accepts enum members, Python types (int/float/str/bool/bytes and the
    datetime types), and alias strings. Native backend dtype objects are NOT
    accepted — use parse_cast_target() (expression casts) or
    registry.from_native() (extraction).

    Raises:
        UnknownDtypeError: input is not a recognizable canonical dtype.
    """
    if isinstance(value, MountainashDtype):
        return value
    if isinstance(value, type):
        if value in _PYTHON_TYPE_MAP:
            return _PYTHON_TYPE_MAP[value]
        dt_map = _datetime_type_map()
        # datetime before date: see _datetime_type_map ordering
        for py_type, dtype in dt_map.items():
            if value is py_type:
                return dtype
    if isinstance(value, str):
        if value in DTYPE_ALIASES:
            return DTYPE_ALIASES[value]
        raise UnknownDtypeError(
            f"Unknown dtype string {value!r}. Use a canonical name like "
            f"'i64', 'string', 'fp64', or a MountainashDtype member."
        )
    if detect_target(value) is not None:
        raise UnknownDtypeError(
            f"{value!r} is a native backend dtype, not a canonical dtype. "
            f"Use parse_cast_target() for expression casts or "
            f"registry.from_native() for extraction."
        )
    raise UnknownDtypeError(
        f"Cannot interpret {value!r} (type {type(value).__name__}) as a dtype."
    )


def parse_cast_target(
    value: Any,
) -> Union[MountainashDtype, DecimalDtype, NativeDtype]:
    """Resolve a user-facing cast target.

    Canonical inputs normalize via parse_dtype. ``DecimalDtype`` passes through
    unchanged. Native backend dtype objects wrap in NativeDtype WITHOUT
    normalization (parameters preserved).
    """
    if isinstance(value, (DecimalDtype, NativeDtype)):
        return value
    try:
        return parse_dtype(value)
    except UnknownDtypeError:
        target = detect_target(value)
        if target is not None:
            return NativeDtype(value=value, target=target)
        raise
