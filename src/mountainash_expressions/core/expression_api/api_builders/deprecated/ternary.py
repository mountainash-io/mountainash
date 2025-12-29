"""Ternary logic operations namespace.

Substrait-aligned implementation using ScalarFunctionNode.

Provides three-valued logic operations where:
- TRUE (1): Definitely true
- UNKNOWN (0): Cannot determine (typically NULL/missing)
- FALSE (-1): Definitely false

All methods prefixed with t_ to distinguish from boolean operations.
Returns integer expressions (-1, 0, 1) for ternary results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .ns_base import BaseExpressionNamespace
from ...expression_nodes import (
    ScalarFunctionNode,
    SingularOrListNode,
    LiteralNode,
    MOUNTAINASH_TERNARY,
)

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ...expression_nodes import ExpressionNode


class TernaryNamespace(BaseExpressionNamespace):
    """
    Ternary logic operations namespace.

    All methods prefixed with t_ to distinguish from boolean operations.
    Returns integer expressions (-1=FALSE, 0=UNKNOWN, 1=TRUE).

    Operations:
    - Comparison: t_eq, t_ne, t_gt, t_lt, t_ge, t_le, t_is_in, t_is_not_in
    - Logical: t_and, t_or, t_not, t_xor, t_xor_parity
    - Constants: (via entry points) always_true, always_false, always_unknown
    - Conversions (ternary->boolean): is_true, is_false, is_unknown, is_known, maybe_true, maybe_false
    - Conversions (boolean->ternary): to_ternary
    """

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
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_EQ,
            arguments=[self._node, other_node],
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
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_NE,
            arguments=[self._node, other_node],
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
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_GT,
            arguments=[self._node, other_node],
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
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_LT,
            arguments=[self._node, other_node],
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
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_GE,
            arguments=[self._node, other_node],
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
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_LE,
            arguments=[self._node, other_node],
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
        # Convert values list to LiteralNodes if needed
        if isinstance(values, (list, tuple, set)):
            options = [LiteralNode(value=v) for v in values]
        else:
            options = [self._to_substrait_node(values)]

        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_IS_IN,
            arguments=[self._node, ScalarFunctionNode(
                function=MOUNTAINASH_TERNARY.LIST,
                arguments=options,
            )],
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
        # Convert values list to LiteralNodes if needed
        if isinstance(values, (list, tuple, set)):
            options = [LiteralNode(value=v) for v in values]
        else:
            options = [self._to_substrait_node(values)]

        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_IS_NOT_IN,
            arguments=[self._node, ScalarFunctionNode(
                function=MOUNTAINASH_TERNARY.LIST,
                arguments=options,
            )],
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
        if not others:
            return self._build(self._node)

        # Chain t_and operations pairwise
        operands = [self._node] + [self._to_substrait_node(other) for other in others]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function=MOUNTAINASH_TERNARY.T_AND,
                arguments=[result, operand],
            )
        return self._build(result)

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
        if not others:
            return self._build(self._node)

        operands = [self._node] + [self._to_substrait_node(other) for other in others]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function=MOUNTAINASH_TERNARY.T_OR,
                arguments=[result, operand],
            )
        return self._build(result)

    def t_not(self) -> BaseExpressionAPI:
        """
        Ternary NOT - sign flip.

        Truth table:
        NOT T = F (-1)
        NOT U = U (0)
        NOT F = T (1)
        """
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.T_NOT,
            arguments=[self._node],
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
        if not others:
            return self._build(self._node)

        operands = [self._node] + [self._to_substrait_node(other) for other in others]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function=MOUNTAINASH_TERNARY.T_XOR,
                arguments=[result, operand],
            )
        return self._build(result)

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
        if not others:
            return self._build(self._node)

        operands = [self._node] + [self._to_substrait_node(other) for other in others]
        result = operands[0]
        for operand in operands[1:]:
            result = ScalarFunctionNode(
                function=MOUNTAINASH_TERNARY.T_XOR_PARITY,
                arguments=[result, operand],
            )
        return self._build(result)

    # ========================================
    # Conversions (Ternary -> Boolean)
    # ========================================

    def is_true(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: TRUE(1) -> True, else -> False.

        This is the strictest booleanizer - only TRUE values become True.
        """
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.IS_TRUE,
            arguments=[self._node],
        )
        return self._build(node)

    def is_false(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: FALSE(-1) -> True, else -> False.

        Returns True only for FALSE ternary values.
        """
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.IS_FALSE,
            arguments=[self._node],
        )
        return self._build(node)

    def is_unknown(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: UNKNOWN(0) -> True, else -> False.

        Returns True only for UNKNOWN ternary values.
        """
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.IS_UNKNOWN,
            arguments=[self._node],
        )
        return self._build(node)

    def is_known(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: TRUE or FALSE -> True, UNKNOWN -> False.

        Returns True for any definite (known) value.
        """
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.IS_KNOWN,
            arguments=[self._node],
        )
        return self._build(node)

    def maybe_true(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: TRUE or UNKNOWN -> True, FALSE -> False.

        This is a lenient booleanizer - gives benefit of doubt to UNKNOWN.
        Useful when you want to include uncertain cases.
        """
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.MAYBE_TRUE,
            arguments=[self._node],
        )
        return self._build(node)

    def maybe_false(self) -> BaseExpressionAPI:
        """
        Convert ternary to boolean: FALSE or UNKNOWN -> True, TRUE -> False.

        Returns True when value might be FALSE (including UNKNOWN).
        """
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.MAYBE_FALSE,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Conversions (Boolean -> Ternary)
    # ========================================

    def to_ternary(self) -> BaseExpressionAPI:
        """
        Convert boolean to ternary: True -> 1, False -> -1.

        Use this to enter "ternary land" from a boolean expression.
        Note: NULL booleans become -1 (FALSE), not 0 (UNKNOWN).
        """
        node = ScalarFunctionNode(
            function=MOUNTAINASH_TERNARY.TO_TERNARY,
            arguments=[self._node],
        )
        return self._build(node)
