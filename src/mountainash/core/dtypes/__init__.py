# src/mountainash/core/dtypes/__init__.py
"""Canonical mountainash dtype system.

Single source of truth for type vocabulary and per-target mappings.
"""
from __future__ import annotations

from .canonical import (
    DTYPE_ALIASES,
    MountainashDtype,
    NativeDtype,
    parse_cast_target,
    parse_dtype,
)
from .casts import SAFE_CASTS, UNSAFE_CASTS, is_safe_cast
from .errors import DtypeMappingError, UnknownDtypeError
from .registry import DtypeRegistry, registry
from .targets import TypeTarget, detect_target


__all__ = [
    "MountainashDtype", "NativeDtype", "DTYPE_ALIASES",
    "parse_dtype", "parse_cast_target",
    "TypeTarget", "detect_target",
    "DtypeRegistry", "registry",
    "UnknownDtypeError", "DtypeMappingError",
    "SAFE_CASTS", "UNSAFE_CASTS", "is_safe_cast",
]
