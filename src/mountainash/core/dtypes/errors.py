"""Typed errors for the canonical dtype system.

`DtypeError` is the subsystem base; both concrete errors share `ValueError`, so
the builtin is mixed in once on the base and inherited transitively — preserving
every existing `except ValueError`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from mountainash.core.errors import MountainashError

if TYPE_CHECKING:
    from .targets import TypeTarget


class DtypeError(MountainashError, ValueError):
    """Base for canonical dtype-system errors."""


class UnknownDtypeError(DtypeError):
    """The input could not be recognized as any dtype."""


class DtypeMappingError(DtypeError):
    """The canonical dtype has no mapping for the requested target/use."""


class InvalidBackendTypeError(DtypeError):
    """A non-empty FieldSpec.backend_type could not be parsed for the target."""

    def __init__(self, field_name: str, backend_type: str, target: "TypeTarget") -> None:
        self.field_name = field_name
        self.backend_type = backend_type
        self.target = target
        super().__init__(
            f"field {field_name!r}: backend_type {backend_type!r} is not a valid "
            f"{target.value} dtype string"
        )
