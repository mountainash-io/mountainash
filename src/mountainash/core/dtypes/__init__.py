# src/mountainash/core/dtypes/__init__.py
"""Canonical mountainash dtype system.

Single source of truth for type vocabulary and per-target mappings.
"""
from __future__ import annotations

from .canonical import (
    ArrayDtype, DTYPE_ALIASES, DecimalDtype, DurationDtype, ListDtype,
    MountainashDtype, NativeDtype, SchemaTypeStatus, StructDtype,
    TimeDtype, TimestampDtype, dtype_family, dtype_is_complete,
    parse_cast_target, parse_dtype,
)
from .casts import SAFE_CASTS, UNSAFE_CASTS, CastSafety, classify_cast, is_safe_cast
from .errors import (
    DtypeError,
    DtypeMappingError,
    InvalidBackendTypeError,
    UnknownDtypeError,
)
from .registry import DtypeRegistry, registry
from .targets import TypeTarget, detect_target


__all__ = [
    "MountainashDtype", "NativeDtype", "DecimalDtype", "TimestampDtype",
    "TimeDtype", "DurationDtype", "ListDtype", "ArrayDtype", "StructDtype",
    "SchemaTypeStatus", "dtype_family", "dtype_is_complete", "DTYPE_ALIASES",
    "parse_dtype", "parse_cast_target", "TypeTarget", "detect_target",
    "DtypeRegistry", "registry", "DtypeError", "UnknownDtypeError",
    "DtypeMappingError", "InvalidBackendTypeError", "SAFE_CASTS",
    "UNSAFE_CASTS", "is_safe_cast", "CastSafety", "classify_cast",
]
