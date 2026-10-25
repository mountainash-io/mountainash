# src/mountainash/core/dtypes/target_ibis.py
"""Ibis native type adapter and mapping tables (string type names — ibis .cast() accepts them)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

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


def _family(native: Any) -> D | None:
    return _FROM_NATIVE.get(_base_name(native))


def _is_complete(native: Any) -> bool:
    if isinstance(native, str):
        return True  # A retained physical SQL description, including unbounded NUMERIC.
    return _base_name(native) != "decimal" or (
        getattr(native, "precision", None) is not None
        and getattr(native, "scale", None) is not None
    )


class IbisTypeAdapter(
    NativeTypeAdapter[Any],
    NativeArrowTransportAdapter[Any, "pa.DataType"],
):
    """Stateless Ibis lowering, decoding, parsing, equivalence and Arrow transport.

    Lowering is logical Ibis datatype construction; it asserts no physical
    fidelity for any SQL dialect.
    """

    target = TypeTarget.IBIS

    @staticmethod
    def _datatype_only(value: Any) -> Any:
        import ibis.expr.datatypes as dt
        if not isinstance(value, dt.DataType):
            raise DtypeMappingError(
                "Physical SQL refinements cannot be represented losslessly by an Ibis dtype"
            )
        return value

    def to_native_schema(self, dtype: CastTarget) -> Any:
        native = native_refinement(dtype, self.target)
        if native is not None:
            return self._datatype_only(native.value)
        if isinstance(dtype, DecimalDtype):
            import ibis.expr.datatypes as dt
            return dt.Decimal(dtype.precision, dtype.scale)
        if isinstance(dtype, PARAMETERIZED_DTYPES):
            return self._lower_parameterized(resolve_dtype_parameters(dtype))
        return lower_scalar(SCHEMA_TYPES, dtype, self.target)

    def to_native_cast(self, dtype: CastTarget) -> Any:
        reject_bare_container_cast(dtype, self.target, SCHEMA_TYPES, CAST_UNSUPPORTED)
        return self.to_native_schema(dtype)

    def _lower_parameterized(self, dtype: Any) -> Any:
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
            child = dtype.element
            return dt.Array(dt.null if child is unknown else self.to_native_schema(child))
        if isinstance(dtype, ArrayDtype):
            child = dtype.element
            value_type = dt.null if child is unknown else self.to_native_schema(child)
            if dtype.dimensions is SchemaTypeStatus.UNKNOWN:
                raise DtypeMappingError("Ibis fixed arrays require known dimensions")
            result = value_type
            for length in reversed(dtype.dimensions):
                result = dt.Array(result, length=length)
            return result
        if isinstance(dtype, StructDtype):
            fields = () if dtype.fields is unknown else dtype.fields
            return dt.Struct.from_tuples(
                (name, dt.null if child is unknown else self.to_native_schema(child))
                for name, child in fields
            )
        raise TypeError(f"Unsupported parameterized Ibis dtype: {dtype!r}")

    def from_native(self, value: Any) -> TypeEvidence:
        import ibis.expr.datatypes as dt

        if isinstance(value, str):
            value = dt.dtype(value)
        if not isinstance(value, dt.DataType):
            raise UnknownDtypeError(f"Unrecognized Ibis dtype: {value!r}")
        name = _base_name(value)
        evidence = NativeDtype(value=value, target=TypeTarget.IBIS)
        refinement = evidence if not value.nullable else None
        if name == "timestamp":
            return TimestampDtype(
                precision=value.scale if value.scale is not None else SchemaTypeStatus.UNKNOWN,
                timezone_aware=value.timezone is not None,
                timezone=value.timezone, native=refinement,
            )
        if name == "time":
            return TimeDtype(native=refinement)
        if name == "interval":
            unit = value.unit.value
            return DurationDtype(
                unit=unit, semantics="calendar" if unit in {"Y", "Q", "M"} else "fixed",
                native=refinement,
            )
        if name == "array":
            element = self.from_native(value.value_type)
            length = getattr(value, "length", None)
            if length is not None:
                dimensions = (length,)
                if isinstance(element, ArrayDtype) and element.native is None:
                    dimensions += element.dimensions
                    element = element.element
                return ArrayDtype(element=element, dimensions=dimensions, native=refinement)
            return ListDtype(element=element, native=refinement)
        if name == "string" and getattr(value, "length", None) is not None:
            return evidence
        if name == "struct":
            return StructDtype(
                fields=tuple((key, self.from_native(child)) for key, child in value.fields.items()),
                native=refinement,
            )
        if name == "decimal":
            try:
                return DecimalDtype(value.precision, value.scale, native=refinement)
            except UnknownDtypeError:
                return evidence
        if name in _FROM_NATIVE and name not in {"float16", "map"}:
            return refinement if refinement is not None else _FROM_NATIVE[name]
        return evidence

    def parse_type_string(self, text: str) -> Optional[Any]:
        try:
            import ibis.expr.datatypes as dt
            return dt.dtype(text)
        except Exception:
            return None

    def types_equal(self, left: Any, right: Any) -> bool:
        import ibis.expr.datatypes as dt
        return dt.dtype(left) == dt.dtype(right)

    def to_arrow_transport(self, value: Any) -> "pa.DataType":
        from ibis.formats.pyarrow import PyArrowType
        return PyArrowType.from_ibis(self._datatype_only(value))
