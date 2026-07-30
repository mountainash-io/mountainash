"""Polars ScalarSetExpressionProtocol implementation.

Implements set membership operations for the Polars backend.
"""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.membership.errors import InternalMembershipError
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarSetExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


def _all_portable_nonnull_literals(members: list) -> bool:
    for v in members:
        if type(v) not in (bool, int, float, str, bytes, date, datetime, Decimal):  # noqa: E721
            return False
        if v is None:
            return False
        if type(v) is float and math.isnan(v):  # noqa: E721
            return False
    return True


def _pl_membership_kernel(needle, members, needle_unknown_fs, member_unknown_fs):
    """Shared Polars membership kernel — single source for boolean + ternary.

    Returns ``(any_match, is_unknown)`` as normalised Polars boolean expressions.
    """
    needle_unknown = needle.is_null().fill_null(True)
    if needle_unknown_fs:
        needle_unknown = needle_unknown | needle.is_in(list(needle_unknown_fs)).fill_null(False)

    if _all_portable_nonnull_literals(members):
        any_match = needle.is_in(members).fill_null(False)
        any_unknown_candidate = pl.lit(False)
    else:
        any_match = pl.lit(False)
        any_unknown_candidate = pl.lit(False)
        for m, ufs in zip(members, member_unknown_fs or [None] * len(members)):
            if m is None:
                eq = pl.lit(False)
            else:
                eq = (needle == m).fill_null(False)
            any_match = any_match | eq
            mu = m.is_null().fill_null(True) if hasattr(m, "is_null") else pl.lit(m is None)
            if ufs:
                mu = mu | (
                    m.is_in(list(ufs)).fill_null(False)
                    if hasattr(m, "is_in")
                    else pl.lit(m in ufs)
                )
            any_unknown_candidate = any_unknown_candidate | mu

    is_unknown = needle_unknown | (~any_match & any_unknown_candidate)
    return any_match, is_unknown


class SubstraitPolarsScalarSetExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarSetExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of ScalarSetExpressionProtocol."""

    def index_in(
        self,
        needle: PolarsExpr,
        /,
        *haystack: PolarsExpr,
    ) -> PolarsExpr:
        if not haystack:
            return pl.lit(-1)
        result = pl.lit(-1)
        for i, value in enumerate(reversed(haystack)):
            idx = len(haystack) - 1 - i
            result = pl.when(needle == value).then(pl.lit(idx)).otherwise(result)
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
        needle: PolarsExpr,
        /,
        *haystack: PolarsExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> PolarsExpr:
        members = self._normalize_members(haystack, member_unknown_values)
        any_match, is_unknown = _pl_membership_kernel(
            needle, members, unknown_values, member_unknown_values
        )
        return pl.when(is_unknown).then(pl.lit(False)).otherwise(any_match)

    def is_not_in(
        self,
        needle: PolarsExpr,
        /,
        *haystack: PolarsExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> PolarsExpr:
        members = self._normalize_members(haystack, member_unknown_values)
        any_match, is_unknown = _pl_membership_kernel(
            needle, members, unknown_values, member_unknown_values
        )
        am = ~any_match
        return pl.when(is_unknown).then(pl.lit(False)).otherwise(am)
