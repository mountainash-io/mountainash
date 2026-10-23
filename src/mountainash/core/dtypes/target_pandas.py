# src/mountainash/core/dtypes/target_pandas.py
"""pandas native type adapter and mapping tables (string dtype names). Imported lazily."""
from __future__ import annotations

from dataclasses import is_dataclass, replace
from typing import TYPE_CHECKING, Any, Optional

from ._lowering import lower_scalar, native_of, native_refinement, reject_bare_container_cast
from .canonical import (
    PARAMETERIZED_DTYPES, ArrayDtype, CastTarget, DecimalDtype, DurationDtype,
    ListDtype, MountainashDtype as D, NativeDtype, SchemaTypeStatus, StructDtype,
    TimestampDtype, resolve_dtype_parameters,
)
from .errors import DtypeMappingError, UnknownDtypeError
from .protocols import NativeArrowTransportAdapter, NativeTypeAdapter, TypeEvidence
from .targets import TypeTarget

if TYPE_CHECKING:
    import pyarrow as pa

SCHEMA_TYPES: dict[D, str] = {
    D.BOOL: "boolean", D.I8: "Int8", D.I16: "Int16", D.I32: "Int32",
    D.I64: "Int64", D.U8: "UInt8", D.U16: "UInt16", D.U32: "UInt32",
    D.U64: "UInt64", D.FP32: "float32", D.FP64: "float64",
    D.STRING: "string", D.BINARY: "object", D.DATE: "datetime64[ns]",
    D.TIME: "object", D.TIMESTAMP: "datetime64[ns]",
    D.DURATION: "timedelta64[ns]", D.LIST: "object", D.STRUCT: "object",
    D.JSON: "string", D.XSD_DURATION: "string",
    D.XSD_YEAR: "string", D.XSD_YEARMONTH: "string",
}

CAST_UNSUPPORTED: frozenset[D] = frozenset({D.LIST, D.STRUCT})

_FROM_NATIVE: dict[str, D] = {
    "string": D.STRING, "str": D.STRING, "object": D.STRING,
    "category": D.STRING,
    "int8": D.I8, "int16": D.I16, "int32": D.I32, "int64": D.I64,
    "Int8": D.I8, "Int16": D.I16, "Int32": D.I32, "Int64": D.I64,
    "uint8": D.U8, "uint16": D.U16, "uint32": D.U32, "uint64": D.U64,
    "UInt8": D.U8, "UInt16": D.U16, "UInt32": D.U32, "UInt64": D.U64,
    "float16": D.FP32, "float32": D.FP32, "float64": D.FP64,
    "Float32": D.FP32, "Float64": D.FP64,
    "bool": D.BOOL, "boolean": D.BOOL,
    "datetime64": D.TIMESTAMP, "period": D.TIMESTAMP,
    "timedelta64": D.DURATION,
}


def _base_name(native: Any) -> str:
    # "datetime64[ns, UTC]" -> "datetime64"; "period[M]" -> "period"
    return str(native).split("[", 1)[0]


def _family(native: Any) -> D | None:
    if _base_name(native) == "object":
        return None
    arrow = getattr(native, "pyarrow_dtype", None)
    if arrow is not None:
        from .target_pyarrow import _family as arrow_family
        return arrow_family(arrow)
    return _FROM_NATIVE.get(_base_name(native))


def _is_complete(native: Any) -> bool:
    return _base_name(native) != "category" or getattr(native, "categories", None) is not None


def _own_arrow_natives(dtype: Any) -> Any:
    """Re-own Arrow native evidence inside an Arrow-decoded dtype as pandas evidence.

    pandas nests through ``pd.ArrowDtype``, so a nested native child or
    refinement of an Arrow-backed column is that level's ``pd.ArrowDtype``: it
    then lowers back through this adapter instead of being rejected as another
    target's override. (pandas cannot carry Arrow field qualifiers, so a
    qualified level keeps its Arrow type only.)
    """
    import pandas as pd
    import pyarrow as pa

    if isinstance(dtype, NativeDtype):
        if dtype.target is not TypeTarget.PYARROW:
            return dtype
        value = dtype.value.type if isinstance(dtype.value, pa.Field) else dtype.value
        return NativeDtype(value=pd.ArrowDtype(value), target=TypeTarget.PANDAS)
    if not is_dataclass(dtype):
        return dtype
    changes: dict[str, Any] = {}
    if getattr(dtype, "native", None) is not None:
        changes["native"] = _own_arrow_natives(dtype.native)
    if isinstance(dtype, (ListDtype, ArrayDtype)):
        changes["element"] = _own_arrow_natives(dtype.element)
    elif isinstance(dtype, StructDtype) and dtype.fields is not SchemaTypeStatus.UNKNOWN:
        changes["fields"] = tuple((name, _own_arrow_natives(child)) for name, child in dtype.fields)
    return replace(dtype, **changes) if changes else dtype


class PandasTypeAdapter(
    NativeTypeAdapter[Any],
    NativeArrowTransportAdapter[Any, "pa.DataType"],
):
    """Stateless pandas lowering, decoding, parsing, equivalence and Arrow transport.

    pandas nests through ``pd.ArrowDtype``: container children are lowered to
    Arrow types, with native pandas children resolved in this domain and
    portable scalars delegated to the Arrow adapter.
    """

    target = TypeTarget.PANDAS

    def to_native_schema(self, dtype: CastTarget) -> Any:
        native = native_refinement(dtype, self.target)
        if native is not None:
            return native.value
        if isinstance(dtype, DecimalDtype):
            import pandas as pd
            import pyarrow as pa
            return pd.ArrowDtype(pa.decimal128(dtype.precision, dtype.scale))
        if isinstance(dtype, PARAMETERIZED_DTYPES):
            return self._lower_parameterized(resolve_dtype_parameters(dtype))
        return lower_scalar(SCHEMA_TYPES, dtype, self.target)

    def to_native_cast(self, dtype: CastTarget) -> Any:
        reject_bare_container_cast(dtype, self.target, SCHEMA_TYPES, CAST_UNSUPPORTED)
        return self.to_native_schema(dtype)

    def _lower_parameterized(self, dtype: Any) -> Any:
        import pandas as pd

        if isinstance(dtype, TimestampDtype):
            precision = dtype.precision
            unit = "us" if precision is SchemaTypeStatus.UNKNOWN else {
                0: "s", 3: "ms", 6: "us", 9: "ns",
            }.get(precision)
            if unit is None:
                raise DtypeMappingError(f"pandas timestamp cannot represent precision {precision}")
            if dtype.timezone_aware is True:
                zone = dtype.timezone
                if zone is None or zone is SchemaTypeStatus.UNKNOWN:
                    zone = "UTC"
                return pd.DatetimeTZDtype(unit=unit, tz=zone)
            if dtype.timezone_aware is False:
                return pd.api.types.pandas_dtype(f"datetime64[{unit}]")
        from .target_pyarrow import lower_parameterized

        return pd.ArrowDtype(lower_parameterized(dtype, self._arrow_child))

    def _arrow_child(self, dtype: Any) -> Any:
        """Arrow type of one nested child inside a pandas ArrowDtype container."""
        from .target_pyarrow import lower_parameterized

        if native_of(dtype) is not None:
            return self.to_arrow_transport(self.to_native_schema(dtype))
        if isinstance(dtype, (D, DecimalDtype)):
            from .registry import registry
            return registry.to_native_schema(dtype, TypeTarget.PYARROW)
        return lower_parameterized(dtype, self._arrow_child)

    def from_native(self, value: Any) -> TypeEvidence:
        import numpy as np
        import pandas as pd
        if isinstance(value, str) and value == "string":
            return D.STRING

        arrow = getattr(value, "pyarrow_dtype", None)
        evidence = NativeDtype(value=value, target=TypeTarget.PANDAS)
        if arrow is not None:
            from .registry import registry
            decoded = registry.from_native(arrow, TypeTarget.PYARROW)
            if isinstance(decoded, NativeDtype):
                return evidence
            decoded = _own_arrow_natives(decoded)
            if is_dataclass(decoded) and decoded.native is not None:
                return replace(decoded, native=evidence)
            return decoded
        precision = {"s": 0, "ms": 3, "us": 6, "ns": 9}
        try:
            normalized = pd.api.types.pandas_dtype(value)
        except (TypeError, ValueError) as error:
            raise UnknownDtypeError(f"Unrecognized pandas dtype: {value!r}") from error
        if isinstance(normalized, pd.DatetimeTZDtype):
            return TimestampDtype(
                precision=precision.get(normalized.unit, SchemaTypeStatus.UNKNOWN),
                timezone_aware=True, timezone=str(normalized.tz),
            )
        if isinstance(normalized, np.dtype):
            if normalized.kind in {"M", "m"}:
                unit, multiplier = np.datetime_data(normalized)
                if normalized.kind == "M":
                    return TimestampDtype(
                        precision=precision.get(unit, SchemaTypeStatus.UNKNOWN),
                        timezone_aware=False, timezone=None,
                        native=evidence if multiplier != 1 else None,
                    )
                return DurationDtype(
                    unit=unit, semantics="calendar" if unit in {"Y", "M"} else "fixed",
                    native=evidence if multiplier != 1 else None,
                )
            name = _base_name(normalized)
            if name in _FROM_NATIVE and name not in {"object", "float16"}:
                return _FROM_NATIVE[name]
        return evidence

    def parse_type_string(self, text: str) -> Optional[str]:
        try:
            import pandas as pd
            pd.api.types.pandas_dtype(text)
            return text
        except (ImportError, TypeError, ValueError):
            return None

    def types_equal(self, left: Any, right: Any) -> bool:
        import pandas as pd
        return pd.api.types.pandas_dtype(left) == pd.api.types.pandas_dtype(right)

    def to_arrow_transport(self, value: Any) -> Any:
        import pandas as pd
        import pyarrow as pa

        normalized = pd.api.types.pandas_dtype(value)
        if isinstance(normalized, pd.ArrowDtype):
            return normalized.pyarrow_dtype
        if isinstance(normalized, pd.DatetimeTZDtype):
            return pa.timestamp(normalized.unit, tz=str(normalized.tz))
        numpy_dtype = getattr(normalized, "numpy_dtype", None)
        if numpy_dtype is not None:
            return pa.from_numpy_dtype(numpy_dtype)
        # An owned empty native value, never a source-frame probe.
        return pa.Array.from_pandas(pd.Series([], dtype=normalized)).type
