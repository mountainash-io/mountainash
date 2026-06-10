# src/mountainash/core/dtypes/errors.py
"""Typed errors for the canonical dtype system.

Both subclass ValueError; backlog item 27 (unified error hierarchy) will
re-parent them under MountainashError via multiple inheritance when it lands.
"""
from __future__ import annotations


class UnknownDtypeError(ValueError):
    """The input could not be recognized as any dtype."""


class DtypeMappingError(ValueError):
    """The canonical dtype has no mapping for the requested target/use."""
