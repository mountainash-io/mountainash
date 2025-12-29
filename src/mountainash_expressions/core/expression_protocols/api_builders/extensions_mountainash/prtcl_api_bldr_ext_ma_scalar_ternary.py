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
from typing import Any, TYPE_CHECKING, Union, Optional, Set, FrozenSet
from typing import Protocol

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode

class MountainAshScalarTernaryAPIBuilderProtocol(Protocol):
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
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary equal to - returns -1/0/1."""
        ...

    def t_ne(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary not equal to - returns -1/0/1."""
        ...

    def t_gt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary greater than - returns -1/0/1."""
        ...

    def t_lt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary less than - returns -1/0/1."""
        ...

    def t_ge(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary greater than or equal - returns -1/0/1."""
        ...

    def t_le(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary less than or equal - returns -1/0/1."""
        ...

    def t_is_in(
        self,
        values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary membership test - returns -1/0/1."""
        ...

    def t_is_not_in(
        self,
        values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary non-membership test - returns -1/0/1."""
        ...

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary AND - minimum of operands."""
        ...

    def t_or(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary OR - maximum of operands."""
        ...

    def t_not(self) -> BaseExpressionAPI:
        """Ternary NOT - sign flip."""
        ...

    def t_xor(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary XOR - exactly one TRUE."""
        ...

    def t_xor_parity(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Ternary XOR parity - odd number of TRUEs."""
        ...


    def always_true_ternary(self) -> BaseExpressionAPI:
        """Return literal TRUE (1)."""
        ...

    def always_false_ternary(self) -> BaseExpressionAPI:
        """Return literal FALSE (-1)."""
        ...

    def always_unknown(self) -> BaseExpressionAPI:
        """Return literal UNKNOWN (0)."""
        ...


    # ========================================
    # Conversions (Ternary -> Boolean)
    # ========================================

    def is_true(self) -> BaseExpressionAPI:
        """TRUE(1) -> True, else -> False."""
        ...

    def is_false(self) -> BaseExpressionAPI:
        """FALSE(-1) -> True, else -> False."""
        ...

    def is_unknown(self) -> BaseExpressionAPI:
        """UNKNOWN(0) -> True, else -> False."""
        ...

    def is_known(self) -> BaseExpressionAPI:
        """TRUE or FALSE -> True, UNKNOWN -> False."""
        ...

    def maybe_true(self) -> BaseExpressionAPI:
        """TRUE or UNKNOWN -> True, FALSE -> False."""
        ...

    def maybe_false(self) -> BaseExpressionAPI:
        """FALSE or UNKNOWN -> True, TRUE -> False."""
        ...

    # ========================================
    # Conversions (Boolean -> Ternary)
    # ========================================

    def to_ternary(self) -> BaseExpressionAPI:
        """True -> 1, False -> -1."""
        ...
