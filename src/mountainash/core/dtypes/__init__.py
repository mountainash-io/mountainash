# src/mountainash/core/dtypes/__init__.py
"""Canonical mountainash dtype system.

Single source of truth for type vocabulary and per-target mappings.
"""
from __future__ import annotations

from typing import Any

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


def resolve_dtype(dtype: Any) -> str:
    """LEGACY (deleted in phase 2): string-returning parse_dtype.

    Kept only for the pre-cutover cast builder / cast systems.
    """
    try:
        return parse_dtype(dtype).value
    except UnknownDtypeError as exc:
        raise ValueError(str(exc)) from exc


__all__ = [
    "MountainashDtype", "NativeDtype", "DTYPE_ALIASES",
    "parse_dtype", "parse_cast_target", "resolve_dtype",
    "TypeTarget", "detect_target",
    "DtypeRegistry", "registry",
    "UnknownDtypeError", "DtypeMappingError",
    "SAFE_CASTS", "UNSAFE_CASTS", "is_safe_cast",
]
