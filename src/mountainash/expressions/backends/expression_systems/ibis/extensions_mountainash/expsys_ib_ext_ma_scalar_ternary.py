"""Ibis TernaryExpressionProtocol implementation.

Implements three-valued logic using Ibis expressions where:
- TRUE = 1
- UNKNOWN = 0
- FALSE = -1

This is a Mountainash extension (not part of Substrait standard).
"""

from __future__ import annotations

from typing import Any, List, Optional, FrozenSet, TYPE_CHECKING
from functools import reduce

import ibis


from ..base import IbisBaseExpressionSystem
from mountainash.expressions.constants import CONST_TERNARY_LOGIC_VALUES

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarTernaryExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr, IbisBooleanExpr, IbisNumericExpr, IbisScalarExpr


# Ternary constants
T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE      # 1
T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN  # 0
T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE    # -1


class MountainAshIbisScalarTernaryExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarTernaryExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of TernaryExpressionProtocol.

    Implements three-valued logic operations for the Ibis backend.
    All comparison operations return integer values (-1, 0, 1).
    """

    # ========================================
    # Helper Methods
    # ========================================

    def _check_unknown(
        self,
        expr: IbisValueExpr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> IbisBooleanExpr|IbisScalarExpr:
        """Check if expression value is in the UNKNOWN set.

        Args:
            expr: Expression to check
            unknown_values: Set of values to treat as UNKNOWN

        Returns:
            Boolean expression that is True if value is UNKNOWN
        """
        if unknown_values is None or unknown_values == frozenset({None}):
            # Default: only NULL is UNKNOWN
            return expr.isnull()

        # Check NULL and sentinel values
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
        """Perform a ternary comparison with UNKNOWN handling.

        Args:
            left: Left operand
            right: Right operand
            comparison: Boolean comparison result
            left_unknown: Set of UNKNOWN values for left operand
            right_unknown: Set of UNKNOWN values for right operand

        Returns:
            Integer expression (-1, 0, 1)
        """
        left_is_unknown = self._check_unknown(left, left_unknown)
        right_is_unknown = self._check_unknown(right, right_unknown)

        # Use nested ifelse: if unknown return UNKNOWN, else if comparison TRUE, else FALSE
        return ibis.ifelse(
            ibis.or_(left_is_unknown, right_is_unknown),
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(comparison, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE)))
        )

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
        """Ternary equality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left == right,
            left_unknown, right_unknown
        )

    def t_ne(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary inequality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left != right,
            left_unknown, right_unknown
        )

    def t_gt(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary greater-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left > right,
            left_unknown, right_unknown
        )

    def t_lt(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary less-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left < right,
            left_unknown, right_unknown
        )

    def t_ge(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary greater-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left >= right,
            left_unknown, right_unknown
        )

    def t_le(
        self,
        left: IbisValueExpr,
        right: IbisValueExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary less-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left <= right,
            left_unknown, right_unknown
        )

    def t_is_in(
        self,
        element: IbisValueExpr,
        collection: List[Any],
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary membership test - returns -1/0/1."""
        is_unknown = self._check_unknown(element, unknown_values)

        return ibis.ifelse(
            is_unknown,
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(element.isin(collection), ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE)))
        )

    def t_is_not_in(
        self,
        element: IbisValueExpr,
        collection: List[Any],
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> IbisValueExpr:
        """Ternary non-membership test - returns -1/0/1."""
        is_unknown = self._check_unknown(element, unknown_values)

        return ibis.ifelse(
            is_unknown,
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(~element.isin(collection), ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE)))
        )

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(self, left: IbisValueExpr, right: IbisValueExpr) -> IbisValueExpr:
        """Ternary AND - minimum of operands."""
        return ibis.least(left, right)

    def t_or(self, left: IbisValueExpr, right: IbisValueExpr) -> IbisValueExpr:
        """Ternary OR - maximum of operands."""
        return ibis.greatest(left, right)

    def t_not(self, operand: IbisValueExpr) -> IbisValueExpr:
        """Ternary NOT - sign flip (TRUE↔FALSE, UNKNOWN stays)."""
        # Simple negation: -operand flips 1 to -1 and vice versa, 0 stays 0
        return (operand * ibis.literal(-1) )

    def t_xor(self, left: IbisValueExpr, right: IbisValueExpr) -> IbisValueExpr:
        """Ternary XOR - exclusive OR.

        Returns TRUE if exactly one is TRUE.
        Returns UNKNOWN if any is UNKNOWN.
        Returns FALSE otherwise.
        """
        is_unknown = (left == ibis.literal(int(T_UNKNOWN))) | (right == ibis.literal(int(T_UNKNOWN)))
        # XOR: one TRUE, one FALSE (using != since ^ isn't available on int)
        is_xor_true = (
            ((left == ibis.literal(int(T_TRUE))) & (right != ibis.literal(int(T_TRUE)))) |
            ((left != ibis.literal(int(T_TRUE))) & (right == ibis.literal(int(T_TRUE))))
        )
        return ibis.ifelse(
            is_unknown,
            ibis.literal(int(T_UNKNOWN)),
            ibis.ifelse(is_xor_true, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE)))
        )

    def t_xor_parity(self, left: IbisValueExpr, right: IbisValueExpr) -> IbisValueExpr:
        """Ternary XOR parity - standard XOR for ternary.

        Same as t_xor for binary case.
        """
        return self.t_xor(left, right)

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> IbisValueExpr:
        """Return literal TRUE (1)."""
        return ibis.literal(int(T_TRUE))

    def always_false_ternary(self) -> IbisValueExpr:
        """Return literal FALSE (-1)."""
        return ibis.literal(int(T_FALSE))

    def always_unknown(self) -> IbisValueExpr:
        """Return literal UNKNOWN (0)."""
        return ibis.literal(int(T_UNKNOWN))

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        """TRUE(1) → True, else → False."""
        # Cast to int to avoid Ibis type coercion issues
        return operand == ibis.literal(int(T_TRUE))

    def is_false_ternary(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        """FALSE(-1) → True, else → False."""
        return operand == ibis.literal(int(T_FALSE))

    def is_unknown(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        """UNKNOWN(0) → True, else → False."""
        return operand == ibis.literal(int(T_UNKNOWN))

    def is_known(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        """TRUE or FALSE → True, UNKNOWN → False."""
        return operand != ibis.literal(int(T_UNKNOWN))

    def maybe_true(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        """TRUE or UNKNOWN → True, FALSE → False."""
        return operand >= ibis.literal(int(T_UNKNOWN))

    def maybe_false(self, operand: IbisValueExpr) -> IbisBooleanExpr:
        """FALSE or UNKNOWN → True, TRUE → False."""
        return operand <= ibis.literal(int(T_UNKNOWN))

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: IbisValueExpr) -> IbisValueExpr:
        """True → 1, False → -1."""
        return ibis.ifelse(operand, ibis.literal(int(T_TRUE)), ibis.literal(int(T_FALSE)))

    # ========================================
    # Utility Functions
    # ========================================

    def collect_values(self, *values: Any) -> List[Any]:
        """Collect values into a list for use in collection operations."""
        return list(values)
