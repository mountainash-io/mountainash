# src/mountainash/core/dtypes/target_python.py
"""Python type-hint native type adapter (dataclass/Pydantic extraction)."""
from __future__ import annotations

import datetime
import decimal
from typing import Any, Optional, get_args, get_origin

from ._lowering import lower_scalar, native_refinement, reject_bare_container_cast
from .canonical import (
    PARAMETERIZED_DTYPES, ArrayDtype, CastTarget, DecimalDtype, DurationDtype,
    ListDtype, MountainashDtype as D, SchemaTypeStatus, StructDtype, TimeDtype,
    TimestampDtype, resolve_dtype_parameters,
)
from .errors import DtypeMappingError, UnknownDtypeError
from .protocols import NativeArrowTransportAdapter, NativeTypeAdapter, TypeEvidence
from .targets import TypeTarget

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

_FROM_TYPE: dict[type, Any] = {
    bool: D.BOOL,  # before int
    int: D.I64,
    float: D.FP64,
    decimal.Decimal: SchemaTypeStatus.UNKNOWN,
    str: D.STRING,
    bytes: D.BINARY,
    datetime.datetime: D.TIMESTAMP,  # before date: datetime subclasses date
    datetime.date: D.DATE,
    datetime.time: D.TIME,
    datetime.timedelta: D.DURATION,
    list: D.LIST,
    tuple: D.LIST,
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


class PythonTypeAdapter(
    NativeTypeAdapter[Any],
    NativeArrowTransportAdapter[Any, Any],
):
    """Stateless Python type-hint lowering and decoding.

    Python hints are carriers, not storage types: they have no Arrow transport
    representation, and lowering rejects detail a hint cannot encode.
    """

    target = TypeTarget.PYTHON

    def to_native_schema(self, dtype: CastTarget) -> Any:
        native = native_refinement(dtype, self.target)
        if native is not None:
            return native.value
        if isinstance(dtype, DecimalDtype):
            return decimal.Decimal
        if isinstance(dtype, PARAMETERIZED_DTYPES):
            return self._lower_parameterized(resolve_dtype_parameters(dtype))
        return lower_scalar(SCHEMA_TYPES, dtype, self.target)

    def to_native_cast(self, dtype: CastTarget) -> Any:
        reject_bare_container_cast(dtype, self.target, SCHEMA_TYPES, CAST_UNSUPPORTED)
        return self.to_native_schema(dtype)

    def _lower_parameterized(self, dtype: Any) -> Any:
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
            child = dtype.element
            return list if child is unknown else list[self.to_native_schema(child)]
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

    def from_native(self, value: Any) -> TypeEvidence:
        # An authored Any is an absent constraint, not missing evidence.
        if value is Any or (isinstance(value, str) and value in _UNTYPED_NAMES):
            return SchemaTypeStatus.UNCONSTRAINED
        origin = get_origin(value)
        if origin is list:
            args = get_args(value)
            return ListDtype(
                element=self.from_native(args[0]) if args else SchemaTypeStatus.UNKNOWN,
            )
        if isinstance(value, type):
            for py_type, dtype in _FROM_TYPE.items():
                if issubclass(value, py_type):
                    return dtype
        if origin is not None and origin in _FROM_TYPE:
            return _FROM_TYPE[origin]
        if isinstance(value, str) and value in _FROM_NAME:
            return _FROM_NAME[value]
        raise UnknownDtypeError(f"Unrecognized Python type hint: {value!r}")

    def parse_type_string(self, text: str) -> Optional[Any]:
        return None  # backend_type strings are never Python hints

    def types_equal(self, left: Any, right: Any) -> bool:
        return left == right

    def to_arrow_transport(self, value: Any) -> Any:
        raise DtypeMappingError(
            f"Python type hint {value!r} has no Arrow transport representation"
        )
