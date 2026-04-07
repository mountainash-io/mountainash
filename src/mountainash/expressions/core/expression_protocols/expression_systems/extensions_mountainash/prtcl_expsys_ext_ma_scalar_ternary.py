"""Ternary logic protocols for three-valued logic operations.

Mountainash Extension: Ternary Logic
URI: file://extensions/functions_ternary.yaml

Ternary logic uses three values:
- TRUE (1): Definitely true
- UNKNOWN (0): Cannot determine (typically NULL/missing)
- FALSE (-1): Definitely false

These protocols enable NULL-aware comparisons and logic operations
where comparisons involving NULL return UNKNOWN instead of FALSE.
"""

from __future__ import annotations
from typing import Any, Collection, FrozenSet, List, Optional, Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarTernaryExpressionSystemProtocol(Protocol[ExpressionT]):
    """
    Backend protocol for ternary logic operations.

    Each backend (Polars, Ibis, Narwhals) implements these methods
    to perform ternary logic operations on their native expressions.
    """

    # ========================================
    # Comparison Operations
    # ========================================

    def t_eq(
        self,
        left: ExpressionT,
        right: ExpressionT,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary equality - returns -1/0/1."""
        ...

    def t_ne(
        self,
        left: ExpressionT,
        right: ExpressionT,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary inequality - returns -1/0/1."""
        ...

    def t_gt(
        self,
        left: ExpressionT,
        right: ExpressionT,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary greater-than - returns -1/0/1."""
        ...

    def t_lt(
        self,
        left: ExpressionT,
        right: ExpressionT,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary less-than - returns -1/0/1."""
        ...

    def t_ge(
        self,
        left: ExpressionT,
        right: ExpressionT,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary greater-than-or-equal - returns -1/0/1."""
        ...

    def t_le(
        self,
        left: ExpressionT,
        right: ExpressionT,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary less-than-or-equal - returns -1/0/1."""
        ...

    def t_is_in(
        self,
        element: ExpressionT,
        collection: Collection[Any],
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary membership test - returns -1/0/1."""
        ...

    def t_is_not_in(
        self,
        element: ExpressionT,
        collection: Collection[Any],
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> ExpressionT:
        """Ternary non-membership test - returns -1/0/1."""
        ...

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(
        self,
        left: ExpressionT,
        right: ExpressionT,
    ) -> ExpressionT:
        """Ternary AND - minimum of operands."""
        ...

    def t_or(
        self,
        left: ExpressionT,
        right: ExpressionT,
    ) -> ExpressionT:
        """Ternary OR - maximum of operands."""
        ...

    def t_not(self, operand: ExpressionT) -> ExpressionT:
        """Ternary NOT - sign flip (TRUE<->FALSE, UNKNOWN stays)."""
        ...

    def t_xor(
        self,
        left: ExpressionT,
        right: ExpressionT,
    ) -> ExpressionT:
        """Ternary XOR - exactly one TRUE."""
        ...

    def t_xor_parity(
        self,
        left: ExpressionT,
        right: ExpressionT,
    ) -> ExpressionT:
        """Ternary XOR parity - odd number of TRUEs."""
        ...

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> ExpressionT:
        """Return literal TRUE (1)."""
        ...

    def always_false_ternary(self) -> ExpressionT:
        """Return literal FALSE (-1)."""
        ...

    def always_unknown(self) -> ExpressionT:
        """Return literal UNKNOWN (0)."""
        ...

    # ========================================
    # Conversions (Ternary -> Boolean)
    # ========================================

    def is_true_ternary(self, operand: ExpressionT) -> ExpressionT:
        """TRUE(1) -> True, else -> False."""
        ...

    def is_false_ternary(self, operand: ExpressionT) -> ExpressionT:
        """FALSE(-1) -> True, else -> False."""
        ...

    def is_unknown(self, operand: ExpressionT) -> ExpressionT:
        """UNKNOWN(0) -> True, else -> False."""
        ...

    def is_known(self, operand: ExpressionT) -> ExpressionT:
        """TRUE or FALSE -> True, UNKNOWN -> False."""
        ...

    def maybe_true(self, operand: ExpressionT) -> ExpressionT:
        """TRUE or UNKNOWN -> True, FALSE -> False."""
        ...

    def maybe_false(self, operand: ExpressionT) -> ExpressionT:
        """FALSE or UNKNOWN -> True, TRUE -> False."""
        ...

    # ========================================
    # Conversions (Boolean -> Ternary)
    # ========================================

    def to_ternary(self, operand: ExpressionT) -> ExpressionT:
        """True -> 1, False -> -1."""
        ...

    # ========================================
    # Utility Functions
    # ========================================

    def collect_values(self, *values: object) -> List[Any]:
        """Collect values into a list for use in collection operations.

        This is a utility function that simply returns its arguments as a list.
        Used internally by t_is_in/t_is_not_in to package collection values.
        """
        ...
