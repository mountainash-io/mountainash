"""Boolean logical operations namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..base import BaseNamespace
from ...protocols import ENUM_BOOLEAN_OPERATORS
from ...expression_nodes import (
    BooleanIterableExpressionNode,
    BooleanUnaryExpressionNode,
)

if TYPE_CHECKING:
    from ...expression_api.base import BaseExpressionAPI
    from ...expression_nodes.base_expression_node import ExpressionNode


class BooleanLogicalNamespace(BaseNamespace):
    """
    Logical operations for boolean expressions.

    Provides logical operators (and_, or_, not_, xor_),
    parity operations, and boolean checks.

    Methods:
        and_: Logical AND
        or_: Logical OR
        xor_: Logical XOR (exclusive or)
        xor_parity: XOR parity (odd number of TRUE)
        not_: Logical NOT
        is_true: Check if TRUE (for ternary logic)
        is_false: Check if FALSE (for ternary logic)
    """

    # ========================================
    # Logical Operators (Iterable)
    # ========================================

    def and_(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical AND operation.

        Args:
            *others: Other expressions to AND with this one.

        Returns:
            New ExpressionAPI with AND node.
        """
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.AND,
            *operands,
        )
        return self._build(node)

    def or_(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical OR operation.

        Args:
            *others: Other expressions to OR with this one.

        Returns:
            New ExpressionAPI with OR node.
        """
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.OR,
            *operands,
        )
        return self._build(node)

    def xor_(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Logical XOR operation (exclusive or).

        Args:
            *others: Other expressions to XOR with this one.

        Returns:
            New ExpressionAPI with XOR node.
        """
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.XOR,
            *operands,
        )
        return self._build(node)

    def xor_parity(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.

        Args:
            *others: Other expressions to check parity with.

        Returns:
            New ExpressionAPI with XOR_PARITY node.
        """
        operands = [self._node] + [self._to_node_or_value(other) for other in others]
        node = BooleanIterableExpressionNode(
            ENUM_BOOLEAN_OPERATORS.XOR_PARITY,
            *operands,
        )
        return self._build(node)

    # ========================================
    # Unary Operators
    # ========================================

    def not_(self) -> BaseExpressionAPI:
        """
        Logical NOT operation.

        Returns:
            New ExpressionAPI with NOT node.
        """
        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.NOT,
            self._node,
        )
        return self._build(node)

    def is_true(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to TRUE (for ternary logic).

        Returns:
            New ExpressionAPI with IS_TRUE node.
        """
        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_TRUE,
            self._node,
        )
        return self._build(node)

    def is_false(self) -> BaseExpressionAPI:
        """
        Check if expression evaluates to FALSE (for ternary logic).

        Returns:
            New ExpressionAPI with IS_FALSE node.
        """
        node = BooleanUnaryExpressionNode(
            ENUM_BOOLEAN_OPERATORS.IS_FALSE,
            self._node,
        )
        return self._build(node)
