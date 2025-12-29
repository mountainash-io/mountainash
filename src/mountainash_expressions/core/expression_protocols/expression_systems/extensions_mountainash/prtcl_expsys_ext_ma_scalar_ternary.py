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
from typing import Any, TYPE_CHECKING, Union, Optional, Set, FrozenSet, List, Protocol

if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions


class MountainAshScalarTernaryExpressionSystemProtocol(Protocol):
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
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary equality - returns -1/0/1."""
        ...

    def t_ne(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary inequality - returns -1/0/1."""
        ...

    def t_gt(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary greater-than - returns -1/0/1."""
        ...

    def t_lt(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary less-than - returns -1/0/1."""
        ...

    def t_ge(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary greater-than-or-equal - returns -1/0/1."""
        ...

    def t_le(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[FrozenSet[Any]] = None,
        right_unknown: Optional[FrozenSet[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary less-than-or-equal - returns -1/0/1."""
        ...

    def t_is_in(
        self,
        element: SupportedExpressions,
        collection: Any,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary membership test - returns -1/0/1."""
        ...

    def t_is_not_in(
        self,
        element: SupportedExpressions,
        collection: Any,
        unknown_values: Optional[FrozenSet[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary non-membership test - returns -1/0/1."""
        ...

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
    ) -> SupportedExpressions:
        """Ternary AND - minimum of operands."""
        ...

    def t_or(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
    ) -> SupportedExpressions:
        """Ternary OR - maximum of operands."""
        ...

    def t_not(self, operand: SupportedExpressions) -> SupportedExpressions:
        """Ternary NOT - sign flip (TRUE<->FALSE, UNKNOWN stays)."""
        ...

    def t_xor(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
    ) -> SupportedExpressions:
        """Ternary XOR - exactly one TRUE."""
        ...

    def t_xor_parity(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
    ) -> SupportedExpressions:
        """Ternary XOR parity - odd number of TRUEs."""
        ...

    # ========================================
    # Constants
    # ========================================

    def always_true_ternary(self) -> SupportedExpressions:
        """Return literal TRUE (1)."""
        ...

    def always_false_ternary(self) -> SupportedExpressions:
        """Return literal FALSE (-1)."""
        ...

    def always_unknown(self) -> SupportedExpressions:
        """Return literal UNKNOWN (0)."""
        ...

    # ========================================
    # Conversions (Ternary -> Boolean)
    # ========================================

    def is_true_ternary(self, operand: SupportedExpressions) -> SupportedExpressions:
        """TRUE(1) -> True, else -> False."""
        ...

    def is_false_ternary(self, operand: SupportedExpressions) -> SupportedExpressions:
        """FALSE(-1) -> True, else -> False."""
        ...

    def is_unknown(self, operand: SupportedExpressions) -> SupportedExpressions:
        """UNKNOWN(0) -> True, else -> False."""
        ...

    def is_known(self, operand: SupportedExpressions) -> SupportedExpressions:
        """TRUE or FALSE -> True, UNKNOWN -> False."""
        ...

    def maybe_true(self, operand: SupportedExpressions) -> SupportedExpressions:
        """TRUE or UNKNOWN -> True, FALSE -> False."""
        ...

    def maybe_false(self, operand: SupportedExpressions) -> SupportedExpressions:
        """FALSE or UNKNOWN -> True, TRUE -> False."""
        ...

    # ========================================
    # Conversions (Boolean -> Ternary)
    # ========================================

    def to_ternary(self, operand: SupportedExpressions) -> SupportedExpressions:
        """True -> 1, False -> -1."""
        ...

    # ========================================
    # Utility Functions
    # ========================================

    def collect_values(self, *values: Any) -> List[Any]:
        """Collect values into a list for use in collection operations.

        This is a utility function that simply returns its arguments as a list.
        Used internally by t_is_in/t_is_not_in to package collection values.
        """
        ...
