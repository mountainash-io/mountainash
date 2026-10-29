"""Typed errors for the validation engine.

Declaration-phase errors raise; execution-phase exceptions are captured
into CheckSummary(status="error") by the runner (spec §6.5) and never
surface as raised exceptions.
"""
from __future__ import annotations

from mountainash.core.errors import MountainashError


class ValidationError(MountainashError):
    """Base for all validation-engine errors."""


class CheckDeclarationError(ValidationError, ValueError):
    """A check is malformed at declaration/classification time.

    Examples: `mostly` on a scalar-valued expression, a literal-only rule,
    an unknown `booleanizer` value.
    """


class IdentityRequiredError(ValidationError, RuntimeError):
    """A keyed-only feature was used without keyed row identity."""


class IdentityInvalidError(ValidationError, ValueError):
    """Declared keyed identity does not hold against the data.

    Key fields missing from the data, or null/duplicate key tuples without
    allow_imperfect_key=True.
    """


class UnknownCheckTypeError(ValidationError, TypeError):
    """The runner received a check kind it cannot execute (closed-by-default)."""
