"""Ternary logic operations namespace.

Provides three-valued logic operations where:
- TRUE (1): Definitely true
- UNKNOWN (0): Cannot determine (typically NULL/missing)
- FALSE (-1): Definitely false

All methods prefixed with t_ to distinguish from boolean operations.
Returns integer expressions (-1, 0, 1) for ternary results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseNamespace
from ..protocols import TernaryBuilderProtocol
from ..protocols.ternary_protocols import ENUM_TERNARY_OPERATORS
from ..expression_nodes import (
    TernaryComparisonExpressionNode,
    TernaryIterableExpressionNode,
    TernaryUnaryExpressionNode,
    TernaryConstantExpressionNode,
    TernaryCollectionExpressionNode,
)
from ..expression_nodes.boolean_expression_nodes import BooleanExpressionNode

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class TernaryNamespace(BaseNamespace, TernaryBuilderProtocol):
    """
    Ternary logic operations namespace.

    All methods prefixed with t_ to distinguish from boolean operations.
    Returns integer expressions (-1=FALSE, 0=UNKNOWN, 1=TRUE).

    Operations:
    - Comparison: t_eq, t_ne, t_gt, t_lt, t_ge, t_le, t_is_in, t_is_not_in
    - Logical: t_and, t_or, t_not, t_xor, t_xor_parity
    - Constants: (via entry points) always_true, always_false, always_unknown
    - Conversions (ternary→boolean): is_true, is_false, is_unknown, is_known, maybe_true, maybe_false
    - Conversions (boolean→ternary): to_ternary
    """

    # ========================================
    # Boolean → Ternary Coercion
    # ========================================

    def _coerce_if_needed(
        self,
        node_or_value: Union[ExpressionNode, Any],
    ) -> Union[ExpressionNode, Any]:
        """
        Auto-coerce boolean expressions to ternary.

        When a boolean expression (e.g., eq, gt result) is used as an operand
        in a ternary operation (e.g., t_and()), automatically wrap it with
        to_ternary() to convert boolean True/False to ternary 1/-1.

        This enables natural chaining like:
            ma.col("active").eq(True).t_and(ma.col("score").t_gt(70))

        Args:
            node_or_value: The node or value to potentially coerce.

        Returns:
            The original input or a TernaryUnaryExpressionNode(TO_TERNARY, ...).
        """
        # Check if this is a boolean node
        if isinstance(node_or_value, BooleanExpressionNode):
            # Auto-wrap with to_ternary() to convert to ternary
            return TernaryUnaryExpressionNode(
                ENUM_TERNARY_OPERATORS.TO_TERNARY,
                node_or_value,
            )

        return node_or_value

    def _get_self_operand(self) -> ExpressionNode:
        """
        Get self._node for use as operand, with boolean coercion if needed.

        When the current node is a boolean expression, it needs to be coerced
        to ternary before use in ternary operations like t_and(), t_or(), etc.

        Returns:
            The self node, potentially wrapped with to_ternary() if boolean.
        """
        return self._coerce_if_needed(self._node)

    # ========================================
    # Comparison Operations (return -1/0/1)
    # ========================================

    def t_eq(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary equal to - returns -1/0/1.

        Returns UNKNOWN (0) if either operand is UNKNOWN.

        Args:
            other: Value or expression to compare with.

        Returns:
            New ExpressionAPI with ternary comparison node.
        """
        other_node = self._to_node_or_value(other)
        node = TernaryComparisonExpressionNode(
            ENUM_TERNARY_OPERATORS.T_EQ,
            self._node,
            other_node,
        )
        return self._build(node)

    def t_ne(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary not equal to - returns -1/0/1.

        Returns UNKNOWN (0) if either operand is UNKNOWN.
        """
        other_node = self._to_node_or_value(other)
        node = TernaryComparisonExpressionNode(
            ENUM_TERNARY_OPERATORS.T_NE,
            self._node,
            other_node,
        )
        return self._build(node)

    def t_gt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary greater than - returns -1/0/1.

        Returns UNKNOWN (0) if either operand is UNKNOWN.
        """
        other_node = self._to_node_or_value(other)
        node = TernaryComparisonExpressionNode(
            ENUM_TERNARY_OPERATORS.T_GT,
            self._node,
            other_node,
        )
        return self._build(node)

    def t_lt(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary less than - returns -1/0/1.

        Returns UNKNOWN (0) if either operand is UNKNOWN.
        """
        other_node = self._to_node_or_value(other)
        node = TernaryComparisonExpressionNode(
            ENUM_TERNARY_OPERATORS.T_LT,
            self._node,
            other_node,
        )
        return self._build(node)

    def t_ge(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary greater than or equal - returns -1/0/1.

        Returns UNKNOWN (0) if either operand is UNKNOWN.
        """
        other_node = self._to_node_or_value(other)
        node = TernaryComparisonExpressionNode(
            ENUM_TERNARY_OPERATORS.T_GE,
            self._node,
            other_node,
        )
        return self._build(node)

    def t_le(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary less than or equal - returns -1/0/1.

        Returns UNKNOWN (0) if either operand is UNKNOWN.
        """
        other_node = self._to_node_or_value(other)
        node = TernaryComparisonExpressionNode(
            ENUM_TERNARY_OPERATORS.T_LE,
            self._node,
            other_node,
        )
        return self._build(node)

    # ========================================
    # Collection Operations
    # ========================================

    def t_is_in(
        self,
        values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary membership test - returns -1/0/1.

        Returns UNKNOWN (0) if the element is UNKNOWN.
        """
        values_node = self._to_node_or_value(values)
        node = TernaryCollectionExpressionNode(
            ENUM_TERNARY_OPERATORS.T_IS_IN,
            None,  # operand (not used by visitor)
            self._node,  # element (used by visitor)
            values_node,  # container
        )
        return self._build(node)

    def t_is_not_in(
        self,
        values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary non-membership test - returns -1/0/1.

        Returns UNKNOWN (0) if the element is UNKNOWN.
        """
        values_node = self._to_node_or_value(values)
        node = TernaryCollectionExpressionNode(
            ENUM_TERNARY_OPERATORS.T_IS_NOT_IN,
            None,  # operand (not used by visitor)
            self._node,  # element (used by visitor)
            values_node,  # container
        )
        return self._build(node)

    # ========================================
    # Logical Operations
    # ========================================

    def t_and(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary AND - minimum of operands.

        Truth table:
        T AND T = T (1)
        T AND U = U (0)
        T AND F = F (-1)
        U AND U = U (0)
        U AND F = F (-1)
        F AND F = F (-1)
        """
        # Use _get_self_operand() to auto-coerce boolean self._node to ternary
        operands = [self._get_self_operand()] + [self._to_node_or_value(other) for other in others]
        node = TernaryIterableExpressionNode(
            ENUM_TERNARY_OPERATORS.T_AND,
            *operands,
        )
        return self._build(node)

    def t_or(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary OR - maximum of operands.

        Truth table:
        T OR T = T (1)
        T OR U = T (1)
        T OR F = T (1)
        U OR U = U (0)
        U OR F = U (0)
        F OR F = F (-1)
        """
        # Use _get_self_operand() to auto-coerce boolean self._node to ternary
        operands = [self._get_self_operand()] + [self._to_node_or_value(other) for other in others]
        node = TernaryIterableExpressionNode(
            ENUM_TERNARY_OPERATORS.T_OR,
            *operands,
        )
        return self._build(node)

    def t_not(self) -> BaseExpressionAPI:
        """
        Ternary NOT - sign flip.

        Truth table:
        NOT T = F (-1)
        NOT U = U (0)
        NOT F = T (1)
        """
        # Use _get_self_operand() to auto-coerce boolean self._node to ternary
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.T_NOT,
            self._get_self_operand(),
        )
        return self._build(node)

    def t_xor(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary XOR - exactly one TRUE.

        Returns TRUE if exactly one operand is TRUE and no operands are UNKNOWN.
        Returns UNKNOWN if any operand is UNKNOWN.
        Returns FALSE otherwise.
        """
        # Use _get_self_operand() to auto-coerce boolean self._node to ternary
        operands = [self._get_self_operand()] + [self._to_node_or_value(other) for other in others]
        node = TernaryIterableExpressionNode(
            ENUM_TERNARY_OPERATORS.T_XOR,
            *operands,
        )
        return self._build(node)

    def t_xor_parity(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Ternary XOR parity - odd number of TRUEs.

        Returns TRUE if odd number of operands are TRUE and no operands are UNKNOWN.
        Returns UNKNOWN if any operand is UNKNOWN.
        Returns FALSE otherwise.
        """
        # Use _get_self_operand() to auto-coerce boolean self._node to ternary
        operands = [self._get_self_operand()] + [self._to_node_or_value(other) for other in others]
        node = TernaryIterableExpressionNode(
            ENUM_TERNARY_OPERATORS.T_XOR_PARITY,
            *operands,
        )
        return self._build(node)

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: TRUE(1) → True, else → False.

        This is the strictest booleanizer - only TRUE values become True.
        """
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.IS_TRUE,
            self._node,
        )
        return self._build(node)

    def is_false(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: FALSE(-1) → True, else → False.

        Returns True only for FALSE ternary values.
        """
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.IS_FALSE,
            self._node,
        )
        return self._build(node)

    def is_unknown(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: UNKNOWN(0) → True, else → False.

        Returns True only for UNKNOWN ternary values.
        """
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.IS_UNKNOWN,
            self._node,
        )
        return self._build(node)

    def is_known(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: TRUE or FALSE → True, UNKNOWN → False.

        Returns True for any definite (known) value.
        """
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.IS_KNOWN,
            self._node,
        )
        return self._build(node)

    def maybe_true(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: TRUE or UNKNOWN → True, FALSE → False.

        This is a lenient booleanizer - gives benefit of doubt to UNKNOWN.
        Useful when you want to include uncertain cases.
        """
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.MAYBE_TRUE,
            self._node,
        )
        return self._build(node)

    def maybe_false(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: FALSE or UNKNOWN → True, TRUE → False.

        Returns True when value might be FALSE (including UNKNOWN).
        """
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.MAYBE_FALSE,
            self._node,
        )
        return self._build(node)

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self) -> BaseExpressionAPI:
        """
        Convert boolean to ternary: True → 1, False → -1.

        Use this to enter "ternary land" from a boolean expression.
        Note: NULL booleans become -1 (FALSE), not 0 (UNKNOWN).
        """
        node = TernaryUnaryExpressionNode(
            ENUM_TERNARY_OPERATORS.TO_TERNARY,
            self._node,
        )
        return self._build(node)
