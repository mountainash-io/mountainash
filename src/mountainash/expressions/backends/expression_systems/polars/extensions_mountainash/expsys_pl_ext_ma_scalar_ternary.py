"""Polars TernaryExpressionProtocol implementation.

Implements three-valued logic using Polars expressions where:
- TRUE = 1
- UNKNOWN = 0
- FALSE = -1

This is a Mountainash extension (not part of Substrait standard).
"""

from __future__ import annotations

from typing import Any, Collection, FrozenSet, List, Optional, TYPE_CHECKING
from functools import reduce

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.constants import CONST_TERNARY_LOGIC_VALUES

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarTernaryExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


# Ternary constants
T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE      # 1
T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN  # 0
T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE    # -1


class MountainAshPolarsScalarTernaryExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarTernaryExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of TernaryExpressionProtocol.

    Implements three-valued logic operations for the Polars backend.
    All comparison operations return integer values (-1, 0, 1).
    """

    # ========================================
    # Helper Methods
    # ========================================

    def _check_unknown(
        self,
        expr: PolarsExpr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Check if expression value is in the UNKNOWN set.

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
        left: PolarsExpr,
        right: PolarsExpr,
        comparison: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
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
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary equality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left == right,
            left_unknown, right_unknown
        )

    def t_ne(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary inequality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left != right,
            left_unknown, right_unknown
        )

    def t_gt(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary greater-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left > right,
            left_unknown, right_unknown
        )

    def t_lt(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary less-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left < right,
            left_unknown, right_unknown
        )

    def t_ge(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary greater-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left >= right,
            left_unknown, right_unknown
        )

    def t_le(
        self,
        left: PolarsExpr,
        right: PolarsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary less-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left <= right,
            left_unknown, right_unknown
        )

    def t_is_in(
        self,
        element: PolarsExpr,
        collection: Collection[Any] | pl.Expr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary membership test - returns -1/0/1.

        `collection` is either a Python list/tuple/set (literal path) or a
        Polars expression resolving to a list-typed column (per-row path).
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, pl.Expr):
            # Expression path: assume list-typed column. If it isn't, Polars
            # raises at collect time with its own clear error. A null list
            # row propagates to UNKNOWN, matching the ternary principle.
            membership = collection.list.contains(element)
            is_unknown = is_unknown | collection.is_null()
        else:
            membership = element.is_in(collection)

        return (
            pl.when(is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(membership)
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    def t_is_not_in(
        self,
        element: PolarsExpr,
        collection: Collection[Any] | pl.Expr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> PolarsExpr:
        """Ternary non-membership test - returns -1/0/1.

        Mirror of `t_is_in`. See its docstring.
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, pl.Expr):
            membership = collection.list.contains(element)
            is_unknown = is_unknown | collection.is_null()
        else:
            membership = element.is_in(collection)

        return (
            pl.when(is_unknown)
            .then(pl.lit(T_UNKNOWN))
            .otherwise(
                pl.when(~membership)
                .then(pl.lit(T_TRUE))
                .otherwise(pl.lit(T_FALSE))
            )
        )

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(self, left: PolarsExpr, right: PolarsExpr) -> PolarsExpr:
        """Ternary AND - minimum of operands."""
        return pl.min_horizontal(left, right)

    def t_or(self, left: PolarsExpr, right: PolarsExpr) -> PolarsExpr:
        """Ternary OR - maximum of operands."""
        return pl.max_horizontal(left, right)

    def t_not(self, operand: PolarsExpr) -> PolarsExpr:
        """Ternary NOT - sign flip (TRUE↔FALSE, UNKNOWN stays)."""
        # Simple negation: -operand flips 1 to -1 and vice versa, 0 stays 0
        return -operand

    def t_xor(self, left: PolarsExpr, right: PolarsExpr) -> PolarsExpr:
        """Ternary XOR - exclusive OR.

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

    def t_xor_parity(self, left: PolarsExpr, right: PolarsExpr) -> PolarsExpr:
        """Ternary XOR parity - standard XOR for ternary.

        Same as t_xor for binary case.
        """
        return self.t_xor(left, right)

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> PolarsExpr:
        """Return literal TRUE (1)."""
        return pl.lit(T_TRUE)

    def always_false_ternary(self) -> PolarsExpr:
        """Return literal FALSE (-1)."""
        return pl.lit(T_FALSE)

    def always_unknown(self) -> PolarsExpr:
        """Return literal UNKNOWN (0)."""
        return pl.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: PolarsExpr) -> PolarsExpr:
        """TRUE(1) → True, else → False."""
        return operand == pl.lit(T_TRUE)

    def is_false_ternary(self, operand: PolarsExpr) -> PolarsExpr:
        """FALSE(-1) → True, else → False."""
        return operand == pl.lit(T_FALSE)

    def is_unknown(self, operand: PolarsExpr) -> PolarsExpr:
        """UNKNOWN(0) → True, else → False."""
        return operand == pl.lit(T_UNKNOWN)

    def is_known(self, operand: PolarsExpr) -> PolarsExpr:
        """TRUE or FALSE → True, UNKNOWN → False."""
        return operand != pl.lit(T_UNKNOWN)

    def maybe_true(self, operand: PolarsExpr) -> PolarsExpr:
        """TRUE or UNKNOWN → True, FALSE → False."""
        return operand >= pl.lit(T_UNKNOWN)

    def maybe_false(self, operand: PolarsExpr) -> PolarsExpr:
        """FALSE or UNKNOWN → True, TRUE → False."""
        return operand <= pl.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: PolarsExpr) -> PolarsExpr:
        """True → 1, False → -1."""
        return (
            pl.when(operand)
            .then(pl.lit(T_TRUE))
            .otherwise(pl.lit(T_FALSE))
        )

    # ========================================
    # Utility Functions
    # ========================================

    def collect_values(self, *values: Any) -> List[Any]:
        """Collect values into a list for use in collection operations."""
        return list(values)
