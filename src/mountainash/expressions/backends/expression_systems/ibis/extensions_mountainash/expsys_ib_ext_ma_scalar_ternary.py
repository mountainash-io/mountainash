"""Ibis TernaryExpressionProtocol implementation.

Implements three-valued logic using Ibis expressions where:
- TRUE = 1
- UNKNOWN = 0
- FALSE = -1

This is a Mountainash extension (not part of Substrait standard).
"""

from __future__ import annotations

from typing import Any, FrozenSet, List, Optional, TYPE_CHECKING
from functools import reduce

import ibis

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.constants import CONST_TERNARY_LOGIC_VALUES
from mountainash.expressions.membership.errors import InternalMembershipError

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarTernaryExpressionSystemProtocol

from .expsys_ib_ext_ma_scalar_set import _ib_membership_kernel

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr, IbisBooleanExpr, IbisNumericExpr, IbisScalarExpr


T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE      # 1
T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN  # 0
T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE    # -1


class MountainAshIbisScalarTernaryExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarTernaryExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of TernaryExpressionProtocol."""

    # ========================================
    # Helper Methods
    # ========================================

    def _check_unknown(
        self,
        expr: IbisValueExpr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> IbisBooleanExpr | IbisScalarExpr:
        if unknown_values is None or unknown_values == frozenset({None}):
            return expr.isnull()
        conditions = []
        if None in unknown_values:
            conditions.append(expr.isnull())
        for val in unknown_values:
            if val is not None:
                conditions.append(expr == ibis.literal(val))
        if not conditions:
            return ibis.literal(False)
        return reduce(lambda x, y: x | y, conditions)

    def _ternary_comparison(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        comparison: IbisNumericExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        left_is_unknown = self._check_unknown(left, left_unknown)
        right_is_unknown = self._check_unknown(right, right_unknown)
        return ibis.ifelse(
            ibis.or_(left_is_unknown, right_is_unknown),
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(comparison, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE))),
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
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        return self._ternary_comparison(left, right, left == right, left_unknown, right_unknown)

    def t_ne(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        return self._ternary_comparison(left, right, left != right, left_unknown, right_unknown)

    def t_gt(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        return self._ternary_comparison(left, right, left > right, left_unknown, right_unknown)

    def t_lt(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        return self._ternary_comparison(left, right, left < right, left_unknown, right_unknown)

    def t_ge(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        return self._ternary_comparison(left, right, left >= right, left_unknown, right_unknown)

    def t_le(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        return self._ternary_comparison(left, right, left <= right, left_unknown, right_unknown)

    def t_is_in(
        self,
        element: IbisValueExpr,
        /,
        *members: IbisValueExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> IbisValueExpr:
        members_list = self._normalize_members(members, member_unknown_values)
        any_match, is_unknown = _ib_membership_kernel(
            element, members_list, unknown_values, member_unknown_values
        )
        return ibis.ifelse(
            is_unknown,
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(any_match, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE))),
        )

    def t_is_not_in(
        self,
        element: IbisValueExpr,
        /,
        *members: IbisValueExpr,
        unknown_values=None,
        member_unknown_values=None,
    ) -> IbisValueExpr:
        members_list = self._normalize_members(members, member_unknown_values)
        any_match, is_unknown = _ib_membership_kernel(
            element, members_list, unknown_values, member_unknown_values
        )
        am = ~any_match
        return ibis.ifelse(
            is_unknown,
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(am, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE))),
        )

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(self, left: IbisValueExpr, right: IbisValueExpr) -> IbisValueExpr:
        return ibis.least(left, right)

    def t_or(self, left: IbisValueExpr, right: IbisValueExpr) -> IbisValueExpr:
        return ibis.greatest(left, right)

    def t_not(self, operand: IbisValueExpr) -> IbisValueExpr:
        return operand * ibis.literal(-1)

    def t_xor(self, left: IbisValueExpr, right: IbisValueExpr) -> IbisValueExpr:
        is_unknown = (left == ibis.literal(int(T_UNKNOWN))) | (right == ibis.literal(int(T_UNKNOWN)))
        is_xor_true = (
            ((left == ibis.literal(int(T_TRUE))) & (right != ibis.literal(int(T_TRUE)))) |
            ((left != ibis.literal(int(T_TRUE))) & (right == ibis.literal(int(T_TRUE))))
        )
        return ibis.ifelse(
            is_unknown,
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(is_xor_true, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE))),
        )

    def t_xor_parity(self, left: IbisValueExpr, right: IbisValueExpr) -> IbisValueExpr:
        return self.t_xor(left, right)

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> IbisValueExpr:
        return ibis.literal(int(T_TRUE))

    def always_false_ternary(self) -> IbisValueExpr:
        return ibis.literal(int(T_FALSE))

    def always_unknown(self) -> IbisValueExpr:
        return ibis.literal(int(T_UNKNOWN))

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        return operand == ibis.literal(int(T_TRUE))

    def is_false_ternary(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        return operand == ibis.literal(int(T_FALSE))

    def is_unknown(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        return operand == ibis.literal(int(T_UNKNOWN))

    def is_known(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        return operand != ibis.literal(int(T_UNKNOWN))

    def maybe_true(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        return operand >= ibis.literal(int(T_UNKNOWN))

    def maybe_false(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        return operand <= ibis.literal(int(T_UNKNOWN))

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: IbisValueExpr) -> IbisValueExpr:
        return ibis.ifelse(operand, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE)))

    # ========================================
    # Utility Functions
    # ========================================

    def collect_values(self, *values: Any) -> List[Any]:
        return list(values)
