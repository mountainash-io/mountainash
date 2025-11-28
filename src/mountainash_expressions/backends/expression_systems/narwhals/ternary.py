"""Narwhals ternary logic operations implementation.

Implements three-valued logic using Narwhals expressions where:
- TRUE = 1
- UNKNOWN = 0
- FALSE = -1
"""

from typing import Any, List, Optional, FrozenSet
from functools import reduce
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import TernaryExpressionProtocol
from ....constants import CONST_TERNARY_LOGIC_VALUES


# Ternary constants
T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE      # 1
T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN  # 0
T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE    # -1


class NarwhalsTernaryExpressionSystem(NarwhalsBaseExpressionSystem, TernaryExpressionProtocol):
    """
    Narwhals implementation of ternary logic operations.

    Implements TernaryExpressionProtocol methods using Narwhals expressions.
    All comparison operations return integer values (-1, 0, 1).
    """

    # ========================================
    # Helper Methods
    # ========================================

    def _check_unknown(
        self,
        expr: nw.Expr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """
        Check if expression value is in the UNKNOWN set.

        Args:
            expr: Expression to check
            unknown_values: Set of values to treat as UNKNOWN

        Returns:
            Boolean expression that is True if value is UNKNOWN
        """
        if unknown_values is None or unknown_values == frozenset({None}):
            # Default: only NULL is UNKNOWN
            return expr.is_null()

        # Check NULL and sentinel values
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
        left: nw.Expr,
        right: nw.Expr,
        comparison: nw.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """
        Perform a ternary comparison with UNKNOWN handling.

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
    # Comparison Operations
    # ========================================

    def t_eq(
        self,
        left: nw.Expr,
        right: nw.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """Ternary equality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left == right,
            left_unknown, right_unknown
        )

    def t_ne(
        self,
        left: nw.Expr,
        right: nw.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """Ternary inequality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left != right,
            left_unknown, right_unknown
        )

    def t_gt(
        self,
        left: nw.Expr,
        right: nw.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """Ternary greater-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left > right,
            left_unknown, right_unknown
        )

    def t_lt(
        self,
        left: nw.Expr,
        right: nw.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """Ternary less-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left < right,
            left_unknown, right_unknown
        )

    def t_ge(
        self,
        left: nw.Expr,
        right: nw.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """Ternary greater-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left >= right,
            left_unknown, right_unknown
        )

    def t_le(
        self,
        left: nw.Expr,
        right: nw.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """Ternary less-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left <= right,
            left_unknown, right_unknown
        )

    def t_is_in(
        self,
        element: nw.Expr,
        collection: List[Any],
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """Ternary membership test - returns -1/0/1."""
        is_unknown = self._check_unknown(element, unknown_values)

        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(element.is_in(collection))
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    def t_is_not_in(
        self,
        element: nw.Expr,
        collection: List[Any],
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> nw.Expr:
        """Ternary non-membership test - returns -1/0/1."""
        is_unknown = self._check_unknown(element, unknown_values)

        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(~element.is_in(collection))
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """Ternary AND - minimum of operands."""
        return nw.min_horizontal(left, right)

    def t_or(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """Ternary OR - maximum of operands."""
        return nw.max_horizontal(left, right)

    def t_not(self, operand: nw.Expr) -> nw.Expr:
        """Ternary NOT - sign flip (TRUE↔FALSE, UNKNOWN stays)."""
        # Multiply by -1: flips 1 to -1 and vice versa, 0 stays 0
        return operand * nw.lit(-1)

    def t_xor(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """
        Ternary XOR - exclusive OR.

        Returns TRUE if exactly one is TRUE.
        Returns UNKNOWN if any is UNKNOWN.
        Returns FALSE otherwise.
        """
        return (
            nw.when((left == nw.lit(T_UNKNOWN)) | (right == nw.lit(T_UNKNOWN)))
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                # XOR: one TRUE, one FALSE
                nw.when(
                    ((left == nw.lit(T_TRUE)) & (right != nw.lit(T_TRUE))) |
                    ((left != nw.lit(T_TRUE)) & (right == nw.lit(T_TRUE)))
                )
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    def t_xor_parity(self, left: nw.Expr, right: nw.Expr) -> nw.Expr:
        """
        Ternary XOR parity - standard XOR for ternary.

        Same as t_xor for binary case.
        """
        return self.t_xor(left, right)

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> nw.Expr:
        """Return literal TRUE (1)."""
        return nw.lit(T_TRUE)

    def always_false_ternary(self) -> nw.Expr:
        """Return literal FALSE (-1)."""
        return nw.lit(T_FALSE)

    def always_unknown(self) -> nw.Expr:
        """Return literal UNKNOWN (0)."""
        return nw.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: nw.Expr) -> nw.Expr:
        """TRUE(1) → True, else → False."""
        return operand == nw.lit(T_TRUE)

    def is_false_ternary(self, operand: nw.Expr) -> nw.Expr:
        """FALSE(-1) → True, else → False."""
        return operand == nw.lit(T_FALSE)

    def is_unknown(self, operand: nw.Expr) -> nw.Expr:
        """UNKNOWN(0) → True, else → False."""
        return operand == nw.lit(T_UNKNOWN)

    def is_known(self, operand: nw.Expr) -> nw.Expr:
        """TRUE or FALSE → True, UNKNOWN → False."""
        return operand != nw.lit(T_UNKNOWN)

    def maybe_true(self, operand: nw.Expr) -> nw.Expr:
        """TRUE or UNKNOWN → True, FALSE → False."""
        return operand >= nw.lit(T_UNKNOWN)

    def maybe_false(self, operand: nw.Expr) -> nw.Expr:
        """FALSE or UNKNOWN → True, TRUE → False."""
        return operand <= nw.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: nw.Expr) -> nw.Expr:
        """True → 1, False → -1."""
        return (
            nw.when(operand)
            .then(nw.lit(T_TRUE))
            .otherwise(nw.lit(T_FALSE))
        )
