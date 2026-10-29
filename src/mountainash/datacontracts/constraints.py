"""Reusable FieldConstraints constants and combinators."""
from __future__ import annotations

from dataclasses import replace
from typing import Any

from mountainash.typespec.spec import FieldConstraints


# --- String patterns ---
SINGLE_CHAR = FieldConstraints(min_length=1, max_length=1)
ISO_DATE = FieldConstraints(min_length=10, max_length=10, pattern=r"\d{4}-\d{2}-\d{2}")
ISO_DATETIME = FieldConstraints(min_length=19, max_length=19, pattern=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
ISO_TIMESTAMP = FieldConstraints(min_length=19, max_length=30, pattern=r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

# --- Numeric ---
POSITIVE_INT = FieldConstraints(required=True, minimum=0)
PERCENTAGE = FieldConstraints(minimum=0, maximum=100)

# --- Combinators ---
def required(base: FieldConstraints) -> FieldConstraints:
    """Return a copy with required=True."""
    return replace(base, required=True)


def with_enum(base: FieldConstraints, values: list[Any]) -> FieldConstraints:
    """Return a copy with enum values added."""
    return replace(base, enum=values)


def with_range(base: FieldConstraints, *, minimum: Any = None, maximum: Any = None) -> FieldConstraints:
    """Return a copy with numeric range."""
    kwargs = {}
    if minimum is not None:
        kwargs["minimum"] = minimum
    if maximum is not None:
        kwargs["maximum"] = maximum
    return replace(base, **kwargs)


def with_length(base: FieldConstraints, *, min_length: int | None = None, max_length: int | None = None) -> FieldConstraints:
    """Return a copy with string length constraints."""
    kwargs = {}
    if min_length is not None:
        kwargs["min_length"] = min_length
    if max_length is not None:
        kwargs["max_length"] = max_length
    return replace(base, **kwargs)
