"""Polars TernaryExpressionProtocol implementation.

Implements three-valued logic using Polars expressions where:
- TRUE = 1
- UNKNOWN = 0
- FALSE = -1

This is a Mountainash extension (not part of Substrait standard).
"""

from __future__ import annotations

from typing import Any, FrozenSet, List, Optional, TYPE_CHECKING
from functools import reduce

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.constants import CONST_TERNARY_LOGIC_VALUES
from mountainash.expressions.membership.errors import InternalMembershipError

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarTernaryExpressionSystemProtocol

from .expsys_pl_ext_ma_scalar_set import _pl_membership_kernel

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE      # 1
T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN  # 0
T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE    # -1


class MountainAshPolarsScalarTernaryExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarTernaryExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of TernaryExpressionProtocol."""

    # ========================================
    # Helper Methods
    # ========================================

    def _check_unknown(
        self,
        expr: PolarsExpr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        if unknown_values is None or unknown_values == frozenset({None}):
            return expr.is_null()
        conditions = []
        if None in unknown_values:
            conditions.append(expr.is_null())
        for val in unknown_values:
            if val is not None:
                conditions.append(expr == pl.lit(val))
        if not conditions:
            return pl.lit(False)
        return reduce(lambda x, y: x | y, conditions)

    def _ternary_comparison(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        comparison: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        left_is_unknown = self._check_unknown(left, left_unknown)
        right_is_unknown = self._check_unknown(right, right_unknown)
        return (
            pl.when(left_is_unknown | right_is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(comparison)
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
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
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        return self._ternary_comparison(left, right, left == right, left_unknown, right_unknown)

    def t_ne(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        return self._ternary_comparison(left, right, left != right, left_unknown, right_unknown)

    def t_gt(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        return self._ternary_comparison(left, right, left > right, left_unknown, right_unknown)

    def t_lt(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        return self._ternary_comparison(left, right, left < right, left_unknown, right_unknown)

    def t_ge(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        return self._ternary_comparison(left, right, left >= right, left_unknown, right_unknown)

    def t_le(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        return self._ternary_comparison(left, right, left <= right, left_unknown, right_unknown)

    def t_is_in(
        self,
        element: PolarsExpr,
        /,
        *members: PolarsExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> PolarsExpr:
        members_list = self._normalize_members(members, member_unknown_values)
        any_match, is_unknown = _pl_membership_kernel(
            element, members_list, unknown_values, member_unknown_values
        )
        return (
            pl.when(is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(any_match)
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    def t_is_not_in(
        self,
        element: PolarsExpr,
        /,
        *members: PolarsExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> PolarsExpr:
        members_list = self._normalize_members(members, member_unknown_values)
        any_match, is_unknown = _pl_membership_kernel(
            element, members_list, unknown_values, member_unknown_values
        )
        am = ~any_match
        return (
            pl.when(is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(am)
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(self, left: PolarsExpr, right: PolarsExpr) -> PolarsExpr:
        return pl.min_horizontal(left, right)

    def t_or(self, left: PolarsExpr, right: PolarsExpr) -> PolarsExpr:
        return pl.max_horizontal(left, right)

    def t_not(self, operand: PolarsExpr) -> PolarsExpr:
        return -operand

    def t_xor(self, left: PolarsExpr, right: PolarsExpr) -> PolarsExpr:
        return (
            pl.when((left == pl.lit(T_UNKNOWN)) | (right == pl.lit(T_UNKNOWN)))
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when((left == pl.lit(T_TRUE)) ^ (right == pl.lit(T_TRUE)))
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    def t_xor_parity(self, left: PolarsExpr, right: PolarsExpr) -> PolarsExpr:
        return self.t_xor(left, right)

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> PolarsExpr:
        return pl.lit(T_TRUE)

    def always_false_ternary(self) -> PolarsExpr:
        return pl.lit(T_FALSE)

    def always_unknown(self) -> PolarsExpr:
        return pl.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: PolarsExpr) -> PolarsExpr:
        return operand == pl.lit(T_TRUE)

    def is_false_ternary(self, operand: PolarsExpr) -> PolarsExpr:
        return operand == pl.lit(T_FALSE)

    def is_unknown(self, operand: PolarsExpr) -> PolarsExpr:
        return operand == pl.lit(T_UNKNOWN)

    def is_known(self, operand: PolarsExpr) -> PolarsExpr:
        return operand != pl.lit(T_UNKNOWN)

    def maybe_true(self, operand: PolarsExpr) -> PolarsExpr:
        return operand >= pl.lit(T_UNKNOWN)

    def maybe_false(self, operand: PolarsExpr) -> PolarsExpr:
        return operand <= pl.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: PolarsExpr) -> PolarsExpr:
        return pl.when(operand).then(pl.lit(T_TRUE)).otherwise(pl.lit(T_FALSE))

    # ========================================
    # Utility Functions
    # ========================================

    def collect_values(self, *values: Any) -> List[Any]:
        return list(values)
