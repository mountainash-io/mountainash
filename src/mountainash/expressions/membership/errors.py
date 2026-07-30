"""Typed errors for membership (is_in / t_is_in) argument validation.

All errors accept an optional offending *value* and render migration guidance
in ``str(e)`` so callers get actionable feedback at the point of failure.
"""
from __future__ import annotations

from typing import Any

from mountainash.core.errors import MountainashError


class MembershipArgumentError(MountainashError):
    """Base error for invalid membership-test arguments."""

    def __init__(self, value: Any = None, *, msg: str | None = None) -> None:
        self.value = value
        super().__init__(msg or f"Invalid membership argument: {value!r}.")


class EmptyMembershipError(MembershipArgumentError):
    """Raised when the collection argument is empty."""

    def __init__(self, value: Any = None) -> None:
        super().__init__(
            value,
            msg="Membership test collection is empty. "
            "A membership test requires at least one value to check against.",
        )


class NestedCollectionError(MembershipArgumentError):
    """Raised when the collection contains nested collections."""

    def __init__(self, value: Any = None) -> None:
        super().__init__(
            value,
            msg="Nested collections are not supported in membership tests. "
            "Flatten the collection or provide a flat iterable instead.",
        )


class BareExpressionCollectionError(MembershipArgumentError):
    """Raised when a bare expression is passed as the *entire collection*.

    Use ``.list.contains()`` or ``.list.t_contains()`` for expression-based
    membership checks on list columns.
    """

    def __init__(self, value: Any = None) -> None:
        super().__init__(
            value,
            msg="A bare expression was passed as the membership-test collection. "
            "Use .list.contains() or .list.t_contains() to check membership "
            "against a list column.",
        )


class NativeExprMemberError(MembershipArgumentError):
    """Raised when a native (non-mountainash) expression is used as a member.

    Use ``ma.col()`` or ``ma.lit()`` to wrap the value as a mountainash
    expression for use inside a set literal.
    """

    def __init__(self, value: Any = None) -> None:
        super().__init__(
            value,
            msg="A native expression was used as a set member in a membership test. "
            "Use ma.col() or ma.lit() for a set member.",
        )


class UnsupportedCollectionError(MembershipArgumentError):
    """Raised when the collection type is not supported."""

    def __init__(self, value: Any = None) -> None:
        super().__init__(
            value,
            msg=f"Unsupported collection type: {type(value).__name__!r}. "
            "Provide a list, tuple, set, or frozenset of values.",
        )
