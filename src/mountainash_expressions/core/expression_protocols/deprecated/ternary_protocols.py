"""Ternary logic protocols for three-valued logic operations.

Ternary logic uses three values:
- TRUE (1): Definitely true
- UNKNOWN (0): Cannot determine (typically NULL/missing)
- FALSE (-1): Definitely false

These protocols enable NULL-aware comparisons and logic operations
where comparisons involving NULL return UNKNOWN instead of FALSE.
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING, Union, Optional, Set
from typing import Protocol

from enum import Enum, auto
from ..constants import CONST_LOGIC_TYPES, ENUM_TERNARY_OPERATORS

if TYPE_CHECKING:
    from ...types import SupportedExpressions
    from ..expression_nodes import ExpressionNode
    from ..namespaces import BaseNamespace


class TernaryVisitorProtocol(Protocol):
    """
    Visitor protocol for ternary logic operations.

    Handles traversal of ternary expression nodes and dispatches
    to appropriate backend operations.
    """

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """Return the logic type (should be TERNARY)."""
        ...

    def visit_expression_node(self, node: Any) -> SupportedExpressions:
        """Visit a ternary expression node and return backend expression."""
        ...

    # ========================================
    # Comparison Operations (return -1/0/1)
    # ========================================

    def t_eq(self, node: Any) -> SupportedExpressions:
        """Ternary equality comparison."""
        ...

    def t_ne(self, node: Any) -> SupportedExpressions:
        """Ternary inequality comparison."""
        ...

    def t_gt(self, node: Any) -> SupportedExpressions:
        """Ternary greater-than comparison."""
        ...

    def t_lt(self, node: Any) -> SupportedExpressions:
        """Ternary less-than comparison."""
        ...

    def t_ge(self, node: Any) -> SupportedExpressions:
        """Ternary greater-than-or-equal comparison."""
        ...

    def t_le(self, node: Any) -> SupportedExpressions:
        """Ternary less-than-or-equal comparison."""
        ...

    def t_is_in(self, node: Any) -> SupportedExpressions:
        """Ternary membership test."""
        ...

    def t_is_not_in(self, node: Any) -> SupportedExpressions:
        """Ternary non-membership test."""
        ...

    # ========================================
    # Logical Operations (min/max semantics)
    # ========================================

    def t_and(self, node: Any) -> SupportedExpressions:
        """Ternary AND (minimum of operands)."""
        ...

    def t_or(self, node: Any) -> SupportedExpressions:
        """Ternary OR (maximum of operands)."""
        ...

    def t_not(self, node: Any) -> SupportedExpressions:
        """Ternary NOT (sign flip, UNKNOWN stays UNKNOWN)."""
        ...

    def t_xor(self, node: Any) -> SupportedExpressions:
        """Ternary XOR (exactly one TRUE)."""
        ...

    def t_xor_parity(self, node: Any) -> SupportedExpressions:
        """Ternary XOR parity (odd number of TRUEs)."""
        ...

    # ========================================
    # Constants
    # ========================================

    def always_true(self, node: Any) -> SupportedExpressions:
        """Return constant TRUE (1)."""
        ...

    def always_false(self, node: Any) -> SupportedExpressions:
        """Return constant FALSE (-1)."""
        ...

    def always_unknown(self, node: Any) -> SupportedExpressions:
        """Return constant UNKNOWN (0)."""
        ...

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true(self, node: Any) -> SupportedExpressions:
        """Convert ternary to boolean: TRUE(1) → True, else → False."""
        ...

    def is_false(self, node: Any) -> SupportedExpressions:
        """Convert ternary to boolean: FALSE(-1) → True, else → False."""
        ...

    def is_unknown(self, node: Any) -> SupportedExpressions:
        """Convert ternary to boolean: UNKNOWN(0) → True, else → False."""
        ...

    def is_known(self, node: Any) -> SupportedExpressions:
        """Convert ternary to boolean: TRUE or FALSE → True, UNKNOWN → False."""
        ...

    def maybe_true(self, node: Any) -> SupportedExpressions:
        """Convert ternary to boolean: TRUE or UNKNOWN → True, FALSE → False."""
        ...

    def maybe_false(self, node: Any) -> SupportedExpressions:
        """Convert ternary to boolean: FALSE or UNKNOWN → True, TRUE → False."""
        ...

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, node: Any) -> SupportedExpressions:
        """Convert boolean to ternary: True → 1, False → -1."""
        ...


class TernaryExpressionProtocol(Protocol):
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
        left_unknown: Optional[Set[Any]] = None,
        right_unknown: Optional[Set[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary equality - returns -1/0/1."""
        ...

    def t_ne(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[Set[Any]] = None,
        right_unknown: Optional[Set[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary inequality - returns -1/0/1."""
        ...

    def t_gt(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[Set[Any]] = None,
        right_unknown: Optional[Set[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary greater-than - returns -1/0/1."""
        ...

    def t_lt(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[Set[Any]] = None,
        right_unknown: Optional[Set[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary less-than - returns -1/0/1."""
        ...

    def t_ge(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[Set[Any]] = None,
        right_unknown: Optional[Set[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary greater-than-or-equal - returns -1/0/1."""
        ...

    def t_le(
        self,
        left: SupportedExpressions,
        right: SupportedExpressions,
        left_unknown: Optional[Set[Any]] = None,
        right_unknown: Optional[Set[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary less-than-or-equal - returns -1/0/1."""
        ...

    def t_is_in(
        self,
        element: SupportedExpressions,
        collection: Any,
        unknown_values: Optional[Set[Any]] = None,
    ) -> SupportedExpressions:
        """Ternary membership test - returns -1/0/1."""
        ...

    def t_is_not_in(
        self,
        element: SupportedExpressions,
        collection: Any,
        unknown_values: Optional[Set[Any]] = None,
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
        """Ternary NOT - sign flip (TRUE↔FALSE, UNKNOWN stays)."""
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
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true_ternary(self, operand: SupportedExpressions) -> SupportedExpressions:
        """TRUE(1) → True, else → False."""
        ...

    def is_false_ternary(self, operand: SupportedExpressions) -> SupportedExpressions:
        """FALSE(-1) → True, else → False."""
        ...

    def is_unknown(self, operand: SupportedExpressions) -> SupportedExpressions:
        """UNKNOWN(0) → True, else → False."""
        ...

    def is_known(self, operand: SupportedExpressions) -> SupportedExpressions:
        """TRUE or FALSE → True, UNKNOWN → False."""
        ...

    def maybe_true(self, operand: SupportedExpressions) -> SupportedExpressions:
        """TRUE or UNKNOWN → True, FALSE → False."""
        ...

    def maybe_false(self, operand: SupportedExpressions) -> SupportedExpressions:
        """FALSE or UNKNOWN → True, TRUE → False."""
        ...

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, operand: SupportedExpressions) -> SupportedExpressions:
        """True → 1, False → -1."""
        ...


class TernaryBuilderProtocol(Protocol):
    """
    Builder protocol for ternary namespace methods.

    Defines the fluent API methods that users call to build
    ternary expressions. Implemented by TernaryNamespace.
    """

    # ========================================
    # Comparison Operations
    # ========================================

    def t_eq(
        self,
        other: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary equal to - returns -1/0/1."""
        ...

    def t_ne(
        self,
        other: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary not equal to - returns -1/0/1."""
        ...

    def t_gt(
        self,
        other: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary greater than - returns -1/0/1."""
        ...

    def t_lt(
        self,
        other: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary less than - returns -1/0/1."""
        ...

    def t_ge(
        self,
        other: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary greater than or equal - returns -1/0/1."""
        ...

    def t_le(
        self,
        other: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary less than or equal - returns -1/0/1."""
        ...

    def t_is_in(
        self,
        values: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary membership test - returns -1/0/1."""
        ...

    def t_is_not_in(
        self,
        values: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary non-membership test - returns -1/0/1."""
        ...

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(
        self,
        *others: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary AND - minimum of operands."""
        ...

    def t_or(
        self,
        *others: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary OR - maximum of operands."""
        ...

    def t_not(self) -> BaseNamespace:
        """Ternary NOT - sign flip."""
        ...

    def t_xor(
        self,
        *others: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary XOR - exactly one TRUE."""
        ...

    def t_xor_parity(
        self,
        *others: Union[BaseNamespace, ExpressionNode, Any],
    ) -> BaseNamespace:
        """Ternary XOR parity - odd number of TRUEs."""
        ...

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true(self) -> BaseNamespace:
        """TRUE(1) → True, else → False."""
        ...

    def is_false(self) -> BaseNamespace:
        """FALSE(-1) → True, else → False."""
        ...

    def is_unknown(self) -> BaseNamespace:
        """UNKNOWN(0) → True, else → False."""
        ...

    def is_known(self) -> BaseNamespace:
        """TRUE or FALSE → True, UNKNOWN → False."""
        ...

    def maybe_true(self) -> BaseNamespace:
        """TRUE or UNKNOWN → True, FALSE → False."""
        ...

    def maybe_false(self) -> BaseNamespace:
        """FALSE or UNKNOWN → True, TRUE → False."""
        ...

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self) -> BaseNamespace:
        """True → 1, False → -1."""
        ...
