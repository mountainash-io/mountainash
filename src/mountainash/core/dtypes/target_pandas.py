# src/mountainash/core/dtypes/target_pandas.py
"""pandas target mappings (string dtype names). Imported lazily."""
from __future__ import annotations

from dataclasses import is_dataclass, replace
from typing import Any, Optional

from .canonical import (
    DecimalDtype, DurationDtype, MountainashDtype as D,
    NativeDtype, SchemaTypeStatus, TimestampDtype,
)
from .targets import TypeTarget
from .errors import DtypeMappingError, UnknownDtypeError


def to_native_parameterized(dtype: Any) -> Any:
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
        return pd.ArrowDtype(_arrow_dtype(dtype))
    return pd.ArrowDtype(_arrow_dtype(dtype))


def _arrow_dtype(dtype: Any) -> Any:
    import pandas as pd
    import pyarrow as pa
    from .registry import registry
    from .target_pyarrow import to_native_parameterized

    if isinstance(dtype, NativeDtype) or getattr(dtype, "native", None) is not None:
        native = pd.api.types.pandas_dtype(registry.to_native_schema(dtype, TypeTarget.PANDAS))
        if isinstance(native, pd.ArrowDtype):
            return native.pyarrow_dtype
        if isinstance(native, pd.DatetimeTZDtype):
            return pa.timestamp(native.unit, tz=str(native.tz))
        numpy_dtype = getattr(native, "numpy_dtype", None)
        if numpy_dtype is not None:
            return pa.from_numpy_dtype(numpy_dtype)
        # This is an owned empty native value, never a source-frame probe.
        return pa.Schema.from_pandas(pd.DataFrame({"value": pd.Series([], dtype=native)})).field("value").type
    if isinstance(dtype, (D, DecimalDtype)):
        return registry.to_native_schema(dtype, TypeTarget.PYARROW)
    return to_native_parameterized(dtype, child_lowerer=_arrow_dtype)

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


def to_native_decimal(dtype: DecimalDtype) -> Any:
    import pyarrow as pa
    import pandas as pd
    return pd.ArrowDtype(pa.decimal128(dtype.precision, dtype.scale))


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


def from_native(native: Any) -> Any:
    import numpy as np
    import pandas as pd
    if isinstance(native, str) and native == "string":
        return D.STRING

    arrow = getattr(native, "pyarrow_dtype", None)
    evidence = NativeDtype(value=native, target=TypeTarget.PANDAS)
    if arrow is not None:
        from .target_pyarrow import from_native as arrow_dtype
        decoded = arrow_dtype(arrow)
        if isinstance(decoded, NativeDtype):
            return evidence
        if is_dataclass(decoded) and decoded.native is not None:
            return replace(decoded, native=evidence)
        return decoded
    precision = {"s": 0, "ms": 3, "us": 6, "ns": 9}
    try:
        normalized = pd.api.types.pandas_dtype(native)
    except (TypeError, ValueError) as error:
        raise UnknownDtypeError(f"Unrecognized pandas dtype: {native!r}") from error
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


def parse_type_string(s: str) -> Optional[str]:
    try:
        import pandas as pd
        pd.api.types.pandas_dtype(s)
        return s
    except (ImportError, TypeError, ValueError):
        return None
