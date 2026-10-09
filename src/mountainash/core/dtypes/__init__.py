# src/mountainash/core/dtypes/__init__.py
"""Canonical mountainash dtype system.

Single source of truth for type vocabulary and per-target mappings.
"""
from __future__ import annotations

from .canonical import (
    CanonicalDtype,
    DecimalDtype,
    DTYPE_ALIASES,
    MountainashDtype,
    NativeDtype,
    parse_cast_target,
    parse_dtype,
)
from .casts import CastSafety, classify_cast, is_safe_cast
from .errors import (
    DtypeError,
    DtypeMappingError,
    InvalidBackendTypeError,
    UnknownDtypeError,
)
from .registry import DtypeRegistry, registry
from .targets import TypeTarget, detect_target


__all__ = [
    "MountainashDtype", "DecimalDtype", "CanonicalDtype", "NativeDtype", "DTYPE_ALIASES",
    "parse_dtype", "parse_cast_target",
    "TypeTarget", "detect_target",
    "DtypeRegistry", "registry",
    "DtypeError", "UnknownDtypeError", "DtypeMappingError", "InvalidBackendTypeError",
    "is_safe_cast",
    "CastSafety", "classify_cast",
]
