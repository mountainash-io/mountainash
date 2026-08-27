"""Root of the mountainash error hierarchy.

`MountainashError` is a deliberately bare marker class: it carries no custom
`__init__`, so subclasses that also inherit a builtin (e.g.
`class MissingResourceSchema(DAGError, ValueError)`) construct exactly as the
builtin did before re-parenting. Structure (codes, context) can be added later
with optional parameters without breaking existing raises.
"""
from __future__ import annotations

from typing import Any


class MountainashError(Exception):
    """Root of all mountainash-raised typed errors."""


class InvalidOptionValueError(MountainashError, ValueError):
    """Raised when a known Substrait option receives an illegal value."""



class CapabilityResidueInvariantError(MountainashError, RuntimeError):
    """A true materialization marker has no declared residue fact."""


class BackendConversionError(MountainashError, TypeError):
    """Raised when a conversion violates a declared backend transit policy."""

    def __init__(
        self,
        message: str,
        *,
        boundary_key: Any,
        source_family: str | None,
        source_dialect: str | None,
        destination_family: str | None,
        destination_dialect: str | None,
        source_type: str,
        route: str,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.boundary_key = boundary_key
        self.source_family = source_family
        self.source_dialect = source_dialect
        self.destination_family = destination_family
        self.destination_dialect = destination_dialect
        self.source_type = source_type
        self.route = route
        self.reason = reason