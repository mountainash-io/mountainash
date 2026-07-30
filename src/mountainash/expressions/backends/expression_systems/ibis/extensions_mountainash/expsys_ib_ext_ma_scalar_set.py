"""Ibis ScalarSetExpressionProtocol implementation.

Implements set membership operations for the Ibis backend.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.membership.errors import InternalMembershipError
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarSetExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


def _all_portable_nonnull_literals(members: list) -> bool:
    for v in members:
        if type(v) not in (bool, int, float, str, bytes, date, datetime, Decimal):  # noqa: E721
            return False
        if v is None:
            return False
        if type(v) is float and math.isnan(v):  # noqa: E721
            return False
    return True


def _ibis_fill_null_false(expr):
    """Coalesce expression to False, replacing NULL with False."""
    return ibis.ifelse(expr.isnull(), ibis.literal(False), expr)


def _ibis_fill_null_true(expr):
    """Coalesce expression to True, replacing NULL with True."""
    return ibis.ifelse(expr.isnull(), ibis.literal(True), expr)


def _ib_membership_kernel(needle, members, needle_unknown_fs, member_unknown_fs):
    """Shared Ibis membership kernel — single source for boolean + ternary.

    Returns ``(any_match, is_unknown)`` as normalised Ibis boolean expressions.
    """
    needle_unknown = needle.isnull()
    if needle_unknown_fs:
        needle_unknown = ibis.or_(
            needle_unknown,
            _ibis_fill_null_false(needle.isin(list(needle_unknown_fs))),
        )

    if _all_portable_nonnull_literals(members):
        any_match = _ibis_fill_null_false(needle.isin(members))
        any_unknown_candidate = ibis.literal(False)
    else:
        any_match = ibis.literal(False)
        any_unknown_candidate = ibis.literal(False)
        for m, ufs in zip(members, member_unknown_fs or [None] * len(members)):
            if m is None:
                eq = ibis.literal(False)
            else:
                eq = _ibis_fill_null_false(needle == m)
            any_match = ibis.or_(any_match, eq)
            mu = _ibis_fill_null_true(m.isnull()) if hasattr(m, "isnull") else ibis.literal(m is None)
            if ufs:
                mu = ibis.or_(
                    mu,
                    _ibis_fill_null_false(m.isin(list(ufs)))
                    if hasattr(m, "isin")
                    else ibis.literal(m in ufs),
                )
            any_unknown_candidate = ibis.or_(any_unknown_candidate, mu)

    is_unknown = ibis.or_(
        needle_unknown,
        ibis.and_(~any_match, any_unknown_candidate),
    )
    return any_match, is_unknown


class SubstraitIbisScalarSetExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarSetExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of ScalarSetExpressionProtocol."""

    def index_in(
        self,
        needle: IbisValueExpr,
        /,
        *haystack: IbisValueExpr,
    ) -> IbisValueExpr:
        if not haystack:
            return ibis.literal(-1)
        result = ibis.literal(-1)
        for i, value in enumerate(reversed(haystack)):
            idx = len(haystack) - 1 - i
            result = ibis.ifelse(needle == value, ibis.literal(idx), result)
        return result

    # ------------------------------------------------------------------
    # normalisation
    # ------------------------------------------------------------------

    def _normalize_members(self, haystack_tuple, member_unknown_values):
        members = (
            haystack_tuple[0]
            if (len(haystack_tuple) == 1 and isinstance(haystack_tuple[0], list))
            else list(haystack_tuple)
        )
        if member_unknown_values is not None and len(member_unknown_values) != len(members):
            raise InternalMembershipError(
                members_len=len(members), muv_len=len(member_unknown_values)
            )
        return members

    # ------------------------------------------------------------------
    # public ops
    # ------------------------------------------------------------------

    def is_in(
        self,
        needle: IbisValueExpr,
        /,
        *haystack: IbisValueExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> IbisValueExpr:
        members = self._normalize_members(haystack, member_unknown_values)
        any_match, is_unknown = _ib_membership_kernel(
            needle, members, unknown_values, member_unknown_values
        )
        return ibis.ifelse(is_unknown, ibis.literal(False), any_match)

    def is_not_in(
        self,
        needle: IbisValueExpr,
        /,
        *haystack: IbisValueExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> IbisValueExpr:
        members = self._normalize_members(haystack, member_unknown_values)
        any_match, is_unknown = _ib_membership_kernel(
            needle, members, unknown_values, member_unknown_values
        )
        am = ~any_match
        return ibis.ifelse(is_unknown, ibis.literal(False), am)
