"""Tests for typed membership error hierarchy."""
from __future__ import annotations

import pytest

from mountainash.core.errors import MountainashError
from mountainash.expressions.membership.errors import (
    BareExpressionCollectionError,
    EmptyMembershipError,
    MembershipArgumentError,
    NativeExprMemberError,
    NestedCollectionError,
    UnsupportedCollectionError,
)


ALL_ERRORS = [
    MembershipArgumentError,
    EmptyMembershipError,
    NestedCollectionError,
    BareExpressionCollectionError,
    NativeExprMemberError,
    UnsupportedCollectionError,
]


class TestMembershipErrorHierarchy:
    """All membership errors are proper MountainashError subclasses."""

    @pytest.mark.parametrize("error_cls", ALL_ERRORS)
    def test_subclasses_mountainash_error(self, error_cls) -> None:
        assert issubclass(error_cls, MountainashError)

    @pytest.mark.parametrize("error_cls", ALL_ERRORS)
    def test_optional_value_arg(self, error_cls) -> None:
        """Each error accepts an optional value argument."""
        obj = error_cls()
        assert obj.value is None

        obj = error_cls(value=[1, 2, 3])
        assert obj.value == [1, 2, 3]

    @pytest.mark.parametrize("error_cls", ALL_ERRORS)
    def test_message_guidance(self, error_cls) -> None:
        """Every error renders non-empty migration guidance in str(e)."""
        msg = str(error_cls())
        assert len(msg) > 0
        assert "." in msg

    def test_bare_expression_collection_error_message(self) -> None:
        """BareExpressionCollectionError mentions .list.contains / .list.t_contains."""
        msg = str(BareExpressionCollectionError())
        assert ".list.contains" in msg
        assert ".list.t_contains" in msg

    def test_native_expr_member_error_message(self) -> None:
        """NativeExprMemberError mentions ma.col / ma.lit."""
        msg = str(NativeExprMemberError())
        assert "ma.col" in msg
        assert "ma.lit" in msg
