"""Narwhals TernaryExpressionProtocol implementation.

Implements three-valued logic using Narwhals expressions where:
- TRUE = 1
- UNKNOWN = 0
- FALSE = -1

This is a Mountainash extension (not part of Substrait standard).
"""

from __future__ import annotations

from typing import Any, Collection, FrozenSet, List, Optional, TYPE_CHECKING
from functools import reduce

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.constants import CONST_TERNARY_LOGIC_VALUES


from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarTernaryExpressionSystemProtocol


if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr

# Ternary constants
T_TRUE = CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE      # 1
T_UNKNOWN = CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN  # 0
T_FALSE = CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE    # -1


class MountainAshNarwhalsScalarTernaryExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarTernaryExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of TernaryExpressionProtocol.

    Implements three-valued logic operations for the Narwhals backend.
    All comparison operations return integer values (-1, 0, 1).
    """

    # ========================================
    # Helper Methods
    # ========================================

    def _check_unknown(
        self,
        expr: NarwhalsExpr,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
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
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary equality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left == right,
            left_unknown, right_unknown
        )

    def t_ne(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary inequality - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left != right,
            left_unknown, right_unknown
        )

    def t_gt(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary greater-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left > right,
            left_unknown, right_unknown
        )

    def t_lt(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary less-than - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left < right,
            left_unknown, right_unknown
        )

    def t_ge(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary greater-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left >= right,
            left_unknown, right_unknown
        )

    def t_le(
        self,
        left: NarwhalsExpr,
        right: NarwhalsExpr,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary less-than-or-equal - returns -1/0/1."""
        return self._ternary_comparison(
            left, right,
            left <= right,
            left_unknown, right_unknown
        )

    def t_is_in(
        self,
        element: NarwhalsExpr,
        collection: Collection[Any] | "NarwhalsExpr",
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary membership test - returns -1/0/1.

        `collection` is a Python collection (literal path) or a narwhals
        expression resolving to a list-typed column (per-row path).
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, nw.Expr):
            membership = collection.list.contains(element)  # pyright: ignore[reportAttributeAccessIssue]
        else:
            membership = element.is_in(collection)

        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(membership)
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    def t_is_not_in(
        self,
        element: NarwhalsExpr,
        collection: Collection[Any] | "NarwhalsExpr",
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> NarwhalsExpr:
        """Ternary non-membership test - returns -1/0/1.

        Mirror of `t_is_in`.
        """
        is_unknown = self._check_unknown(element, unknown_values)

        if isinstance(collection, nw.Expr):
            membership = collection.list.contains(element)  # pyright: ignore[reportAttributeAccessIssue]
        else:
            membership = element.is_in(collection)

        return (
            nw.when(is_unknown)
            .then(nw.lit(T_UNKNOWN))
            .otherwise(
                nw.when(~membership)
                .then(nw.lit(T_TRUE))
                .otherwise(nw.lit(T_FALSE))
            )
        )

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(self, left: NarwhalsExpr, right: NarwhalsExpr) -> NarwhalsExpr:
        """Ternary AND - minimum of operands.

        Uses when/then instead of nw.min_horizontal to avoid narwhals-pandas
        DuplicateError on intermediate 'literal' column names (#77).
        """
        return nw.when(left < right).then(left).otherwise(right)

    def t_or(self, left: NarwhalsExpr, right: NarwhalsExpr) -> NarwhalsExpr:
        """Ternary OR - maximum of operands.

        Uses when/then instead of nw.max_horizontal to avoid narwhals-pandas
        DuplicateError on intermediate 'literal' column names (#77).
        """
        return nw.when(left > right).then(left).otherwise(right)

    def t_not(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        """Ternary NOT - sign flip (TRUE↔FALSE, UNKNOWN stays)."""
        # Multiply by -1: flips 1 to -1 and vice versa, 0 stays 0
        return operand * nw.lit(-1)

    def t_xor(self, left: NarwhalsExpr, right: NarwhalsExpr) -> NarwhalsExpr:
        """Ternary XOR - exclusive OR.

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

    def t_xor_parity(self, left: NarwhalsExpr, right: NarwhalsExpr) -> NarwhalsExpr:
        """Ternary XOR parity - standard XOR for ternary.

        Same as t_xor for binary case.
        """
        return self.t_xor(left, right)

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> NarwhalsExpr:
        """Return literal TRUE (1)."""
        return nw.lit(T_TRUE)

    def always_false_ternary(self) -> NarwhalsExpr:
        """Return literal FALSE (-1)."""
        return nw.lit(T_FALSE)

    def always_unknown(self) -> NarwhalsExpr:
        """Return literal UNKNOWN (0)."""
        return nw.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        """TRUE(1) → True, else → False."""
        return operand == nw.lit(T_TRUE)

    def is_false_ternary(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        """FALSE(-1) → True, else → False."""
        return operand == nw.lit(T_FALSE)

    def is_unknown(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        """UNKNOWN(0) → True, else → False."""
        return operand == nw.lit(T_UNKNOWN)

    def is_known(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        """TRUE or FALSE → True, UNKNOWN → False."""
        return operand != nw.lit(T_UNKNOWN)

    def maybe_true(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        """TRUE or UNKNOWN → True, FALSE → False."""
        return operand >= nw.lit(T_UNKNOWN)

    def maybe_false(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        """FALSE or UNKNOWN → True, TRUE → False."""
        return operand <= nw.lit(T_UNKNOWN)

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: NarwhalsExpr) -> NarwhalsExpr:
        """True → 1, False → -1."""
        return (
            nw.when(operand)
            .then(nw.lit(T_TRUE))
            .otherwise(nw.lit(T_FALSE))
        )

    # ========================================
    # Utility Functions
    # ========================================

    def collect_values(self, *values: Any) -> List[Any]:
        """Collect values into a list for use in collection operations."""
        return list(values)
