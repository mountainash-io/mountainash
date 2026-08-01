"""Narwhals TernaryExpressionProtocol implementation.

Implements three-valued logic using Narwhals expressions where:
- TRUE = 1
- UNKNOWN = 0
- FALSE = -1

This is a Mountainash extension (not part of Substrait standard).
"""

from __future__ import annotations

from typing import Any, FrozenSet, List, Optional, TYPE_CHECKING
from functools import reduce

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.constants import CONST_TERNARY_LOGIC_VALUES
from mountainash.expressions.membership.errors import InternalMembershipError

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarTernaryExpressionSystemProtocol

from .expsys_nw_ext_ma_scalar_set import _nw_membership_kernel

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE      # 1
T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN  # 0
T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE    # -1


class MountainAshNarwhalsScalarTernaryExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarTernaryExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of TernaryExpressionProtocol."""

    # ========================================
    # Helper Methods
    # ========================================

    def _check_unknown(
        self,
        expr: NarwhalsExpr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        if unknown_values is None or unknown_values == frozenset({None}):
            return expr.is_null()
        conditions = []
        if None in unknown_values:
            conditions.append(expr.is_null())
        for val in unknown_values:
            if val is not None:
                conditions.append(expr == nw.lit(val))
        if not conditions:
            return nw.lit(False)
        return reduce(lambda x, y: x | y, conditions)

    def _ternary_comparison(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        comparison: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        left_is_unknown = self._check_unknown(left, left_unknown)
        right_is_unknown = self._check_unknown(right, right_unknown)
        return (
            nw.when(left_is_unknown | right_is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(comparison)
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    # ========================================
    # normalisation
    # ========================================

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

    # ========================================
    # Comparison Operations
    # ========================================

    def t_eq(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        return self._ternary_comparison(left, right, left == right, left_unknown, right_unknown)

    def t_ne(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        return self._ternary_comparison(left, right, left != right, left_unknown, right_unknown)

    def t_gt(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        return self._ternary_comparison(left, right, left > right, left_unknown, right_unknown)

    def t_lt(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        return self._ternary_comparison(left, right, left < right, left_unknown, right_unknown)

    def t_ge(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        return self._ternary_comparison(left, right, left >= right, left_unknown, right_unknown)

    def t_le(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        return self._ternary_comparison(left, right, left <= right, left_unknown, right_unknown)

    def t_is_in(
        self,
        element: NarwhalsExpr,
        /,
        *members: NarwhalsExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> NarwhalsExpr:
        members_list = self._normalize_members(members, member_unknown_values)
        any_match, is_unknown = _nw_membership_kernel(
            element, members_list, unknown_values, member_unknown_values
        )
        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(any_match)
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    def t_is_not_in(
        self,
        element: NarwhalsExpr,
        /,
        *members: NarwhalsExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> NarwhalsExpr:
        members_list = self._normalize_members(members, member_unknown_values)
        any_match, is_unknown = _nw_membership_kernel(
            element, members_list, unknown_values, member_unknown_values
        )
        am = ~any_match
        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(am)
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(self, left: NarwhalsExpr, right: NarwhalsExpr) -> NarwhalsExpr:
        return nw.when(left < right).then(left).otherwise(right)

    def t_or(self, left: NarwhalsExpr, right: NarwhalsExpr) -> NarwhalsExpr:
        return nw.when(left > right).then(left).otherwise(right)

    def t_not(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        return operand * nw.lit(-1)

    def t_xor(self, left: NarwhalsExpr, right: NarwhalsExpr) -> NarwhalsExpr:
        return (
            nw.when((left == nw.lit(T_UNKNOWN)) | (right == nw.lit(T_UNKNOWN)))
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(
                    ((left == nw.lit(T_TRUE)) & (right != nw.lit(T_TRUE))) |
                    ((left != nw.lit(T_TRUE)) & (right == nw.lit(T_TRUE)))
                )
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    def t_xor_parity(self, left: NarwhalsExpr, right: NarwhalsExpr) -> NarwhalsExpr:
        return self.t_xor(left, right)

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> NarwhalsExpr:
        return nw.lit(T_TRUE)

    def always_false_ternary(self) -> NarwhalsExpr:
        return nw.lit(T_FALSE)

    def always_unknown(self) -> NarwhalsExpr:
        return nw.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        return operand == nw.lit(T_TRUE)

    def is_false_ternary(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        return operand == nw.lit(T_FALSE)

    def is_unknown(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        return operand == nw.lit(T_UNKNOWN)

    def is_known(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        return operand != nw.lit(T_UNKNOWN)

    def maybe_true(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        return operand >= nw.lit(T_UNKNOWN)

    def maybe_false(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        return operand <= nw.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        return (
            nw.when(operand.is_null()).then(nw.lit(T_UNKNOWN))
            .when(operand).then(nw.lit(T_TRUE))
            .otherwise(nw.lit(T_FALSE))
        )

    # ========================================
    # Utility Functions
    # ========================================

    def collect_values(self, *values: Any) -> List[Any]:
        return list(values)
