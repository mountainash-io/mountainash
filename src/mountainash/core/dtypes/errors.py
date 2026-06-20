"""Typed errors for the canonical dtype system.

`DtypeError` is the subsystem base; both concrete errors share `ValueError`, so
the builtin is mixed in once on the base and inherited transitively — preserving
every existing `except ValueError`.
"""
from __future__ import annotations

from mountainash.core.errors import MountainashError


class DtypeError(MountainashError, ValueError):
    """Base for canonical dtype-system errors."""


class UnknownDtypeError(DtypeError):
    """The input could not be recognized as any dtype."""


class DtypeMappingError(DtypeError):
    """The canonical dtype has no mapping for the requested target/use."""
