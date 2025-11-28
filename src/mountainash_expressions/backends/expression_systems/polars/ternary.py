"""Polars ternary logic operations implementation.

Implements three-valued logic using Polars expressions where:
- TRUE = 1
- UNKNOWN = 0
- FALSE = -1
"""

from typing import Any, List, Optional, Set, FrozenSet
from functools import reduce
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import TernaryExpressionProtocol
from ....constants import CONST_TERNARY_LOGIC_VALUES


# Ternary constants
T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE      # 1
T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN  # 0
T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE    # -1


class PolarsTernaryExpressionSystem(PolarsBaseExpressionSystem, TernaryExpressionProtocol):
    """
    Polars implementation of ternary logic operations.

    Implements TernaryExpressionProtocol methods using Polars expressions.
    All comparison operations return integer values (-1, 0, 1).
    """

    # ========================================
    # Helper Methods
    # ========================================

    def _check_unknown(
        self,
        expr: pl.Expr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
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
                conditions.append(expr == pl.lit(val))

        if not conditions:
            return pl.lit(False)

        return reduce(lambda x, y: x | y, conditions)

    def _ternary_comparison(
        self,
        left: pl.Expr,
        right: pl.Expr,
        comparison: pl.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
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
            pl.when(left_is_unknown | right_is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(comparison)
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    # ========================================
    # Comparison Operations
    # ========================================

    def t_eq(
        self,
        left: pl.Expr,
        right: pl.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
        """Ternary equality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left == right,
            left_unknown, right_unknown
        )

    def t_ne(
        self,
        left: pl.Expr,
        right: pl.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
        """Ternary inequality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left != right,
            left_unknown, right_unknown
        )

    def t_gt(
        self,
        left: pl.Expr,
        right: pl.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
        """Ternary greater-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left > right,
            left_unknown, right_unknown
        )

    def t_lt(
        self,
        left: pl.Expr,
        right: pl.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
        """Ternary less-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left < right,
            left_unknown, right_unknown
        )

    def t_ge(
        self,
        left: pl.Expr,
        right: pl.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
        """Ternary greater-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left >= right,
            left_unknown, right_unknown
        )

    def t_le(
        self,
        left: pl.Expr,
        right: pl.Expr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
        """Ternary less-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left <= right,
            left_unknown, right_unknown
        )

    def t_is_in(
        self,
        element: pl.Expr,
        collection: List[Any],
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
        """Ternary membership test - returns -1/0/1."""
        is_unknown = self._check_unknown(element, unknown_values)

        return (
            pl.when(is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(element.is_in(collection))
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    def t_is_not_in(
        self,
        element: pl.Expr,
        collection: List[Any],
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> pl.Expr:
        """Ternary non-membership test - returns -1/0/1."""
        is_unknown = self._check_unknown(element, unknown_values)

        return (
            pl.when(is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(~element.is_in(collection))
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary AND - minimum of operands."""
        return pl.min_horizontal(left, right)

    def t_or(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """Ternary OR - maximum of operands."""
        return pl.max_horizontal(left, right)

    def t_not(self, operand: pl.Expr) -> pl.Expr:
        """Ternary NOT - sign flip (TRUE↔FALSE, UNKNOWN stays)."""
        # Simple negation: -operand flips 1 to -1 and vice versa, 0 stays 0
        return -operand

    def t_xor(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """
        Ternary XOR - exclusive OR.

        Returns TRUE if exactly one is TRUE.
        Returns UNKNOWN if any is UNKNOWN.
        Returns FALSE otherwise.
        """
        # If either is UNKNOWN (0), result is UNKNOWN
        # If both TRUE or both FALSE, result is FALSE
        # If exactly one TRUE, result is TRUE
        return (
            pl.when((left == pl.lit(T_UNKNOWN)) | (right == pl.lit(T_UNKNOWN)))
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                # XOR: one TRUE, one FALSE
                pl.when((left == pl.lit(T_TRUE)) ^ (right == pl.lit(T_TRUE)))
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    def t_xor_parity(self, left: pl.Expr, right: pl.Expr) -> pl.Expr:
        """
        Ternary XOR parity - standard XOR for ternary.

        Same as t_xor for binary case.
        """
        return self.t_xor(left, right)

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> pl.Expr:
        """Return literal TRUE (1)."""
        return pl.lit(T_TRUE)

    def always_false_ternary(self) -> pl.Expr:
        """Return literal FALSE (-1)."""
        return pl.lit(T_FALSE)

    def always_unknown(self) -> pl.Expr:
        """Return literal UNKNOWN (0)."""
        return pl.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: pl.Expr) -> pl.Expr:
        """TRUE(1) → True, else → False."""
        return operand == pl.lit(T_TRUE)

    def is_false_ternary(self, operand: pl.Expr) -> pl.Expr:
        """FALSE(-1) → True, else → False."""
        return operand == pl.lit(T_FALSE)

    def is_unknown(self, operand: pl.Expr) -> pl.Expr:
        """UNKNOWN(0) → True, else → False."""
        return operand == pl.lit(T_UNKNOWN)

    def is_known(self, operand: pl.Expr) -> pl.Expr:
        """TRUE or FALSE → True, UNKNOWN → False."""
        return operand != pl.lit(T_UNKNOWN)

    def maybe_true(self, operand: pl.Expr) -> pl.Expr:
        """TRUE or UNKNOWN → True, FALSE → False."""
        return operand >= pl.lit(T_UNKNOWN)

    def maybe_false(self, operand: pl.Expr) -> pl.Expr:
        """FALSE or UNKNOWN → True, TRUE → False."""
        return operand <= pl.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: pl.Expr) -> pl.Expr:
        """True → 1, False → -1."""
        return (
            pl.when(operand)
            .then(pl.lit(T_TRUE))
            .otherwise(pl.lit(T_FALSE))
        )
