"""Ternary logic expression visitor for three-valued logic operations.

Handles traversal of ternary expression nodes and dispatches to
appropriate backend operations via the injected ExpressionSystem.

Ternary logic uses three values:
- TRUE (1): Definitely true
- UNKNOWN (0): Cannot determine (typically NULL/missing)
- FALSE (-1): Definitely false
"""

from __future__ import annotations
from typing import Callable, Dict, TYPE_CHECKING, Any, Set, FrozenSet
from enum import Enum
from functools import reduce

from .expression_visitor import ExpressionVisitor
from ..expression_parameters import ExpressionParameter
from ..constants import CONST_LOGIC_TYPES, ENUM_TERNARY_OPERATORS
from ...types import SupportedExpressions

from ..expression_nodes import (
    TernaryComparisonExpressionNode,
    TernaryIterableExpressionNode,
    TernaryUnaryExpressionNode,
    TernaryConstantExpressionNode,
    TernaryCollectionExpressionNode,
    TernaryColumnExpressionNode,
    SupportedTernaryExpressionNodeTypes,
)

from ..protocols import TernaryVisitorProtocol

if TYPE_CHECKING:
    pass


# Default UNKNOWN values - just NULL by default
DEFAULT_UNKNOWN_VALUES: FrozenSet[Any] = frozenset({None})


class TernaryExpressionVisitor(ExpressionVisitor, TernaryVisitorProtocol):
    """
    Visitor for ternary expression nodes.

    Handles three-valued logic where comparisons with NULL return UNKNOWN,
    and logical operations use min/max semantics.

    Works with any backend through the injected ExpressionSystem.
    """

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """Return the logic type for this visitor."""
        return CONST_LOGIC_TYPES.TERNARY

    # ===============
    # Operations Maps
    # ===============

    @property
    def _ternary_ops(self) -> Dict[Enum, Callable]:
        """Map of operators to visitor methods."""
        return {
            # Column reference
            ENUM_TERNARY_OPERATORS.T_COL: self.t_col,

            # Comparisons
            ENUM_TERNARY_OPERATORS.T_EQ: self.t_eq,
            ENUM_TERNARY_OPERATORS.T_NE: self.t_ne,
            ENUM_TERNARY_OPERATORS.T_GT: self.t_gt,
            ENUM_TERNARY_OPERATORS.T_LT: self.t_lt,
            ENUM_TERNARY_OPERATORS.T_GE: self.t_ge,
            ENUM_TERNARY_OPERATORS.T_LE: self.t_le,
            ENUM_TERNARY_OPERATORS.T_IS_IN: self.t_is_in,
            ENUM_TERNARY_OPERATORS.T_IS_NOT_IN: self.t_is_not_in,

            # Logical
            ENUM_TERNARY_OPERATORS.T_AND: self.t_and,
            ENUM_TERNARY_OPERATORS.T_OR: self.t_or,
            ENUM_TERNARY_OPERATORS.T_NOT: self.t_not,
            ENUM_TERNARY_OPERATORS.T_XOR: self.t_xor,
            ENUM_TERNARY_OPERATORS.T_XOR_PARITY: self.t_xor_parity,

            # Constants
            ENUM_TERNARY_OPERATORS.ALWAYS_TRUE: self.always_true,
            ENUM_TERNARY_OPERATORS.ALWAYS_FALSE: self.always_false,
            ENUM_TERNARY_OPERATORS.ALWAYS_UNKNOWN: self.always_unknown,

            # Conversions (ternary → boolean)
            ENUM_TERNARY_OPERATORS.IS_TRUE: self.is_true,
            ENUM_TERNARY_OPERATORS.IS_FALSE: self.is_false,
            ENUM_TERNARY_OPERATORS.IS_UNKNOWN: self.is_unknown,
            ENUM_TERNARY_OPERATORS.IS_KNOWN: self.is_known,
            ENUM_TERNARY_OPERATORS.MAYBE_TRUE: self.maybe_true,
            ENUM_TERNARY_OPERATORS.MAYBE_FALSE: self.maybe_false,

            # Conversions (boolean → ternary)
            ENUM_TERNARY_OPERATORS.TO_TERNARY: self.to_ternary,
        }

    # ===============
    # Main Dispatch
    # ===============

    def visit_expression_node(self, node: SupportedTernaryExpressionNodeTypes) -> SupportedExpressions:
        """Visit a ternary expression node and dispatch to appropriate method."""
        op_func = self._get_expr_op(self._ternary_ops, node)
        return op_func(node)

    # ===============
    # Helper Methods
    # ===============

    def _get_unknown_values(self, node: Any) -> FrozenSet[Any]:
        """
        Extract unknown values from a node or return defaults.

        For TernaryColumnExpressionNode, returns the configured unknown_values.
        For other nodes, returns the default (just NULL).
        """
        if isinstance(node, TernaryColumnExpressionNode):
            return node.unknown_values
        return DEFAULT_UNKNOWN_VALUES

    def _to_native_with_unknown(
        self,
        node: Any,
    ) -> tuple[SupportedExpressions, FrozenSet[Any]]:
        """
        Convert a node to native expression and extract unknown values.

        Returns:
            Tuple of (native_expression, unknown_values)
        """
        unknown_values = self._get_unknown_values(node)
        native_expr = ExpressionParameter(node, expression_system=self.backend).to_native_expression()
        return native_expr, unknown_values

    # ========================================
    # Column Reference
    # ========================================

    def t_col(self, node: TernaryColumnExpressionNode) -> SupportedExpressions:
        """
        Convert ternary column reference to native column expression.

        The unknown_values are carried by the node and used by comparison
        operations that consume this column reference.
        """
        return self.backend.col(node.column)

    # ========================================
    # Comparison Operations (return -1/0/1)
    # ========================================

    def t_eq(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions:
        """Ternary equality: UNKNOWN if either operand is UNKNOWN."""
        left_expr, left_unknown = self._to_native_with_unknown(node.left)
        right_expr, right_unknown = self._to_native_with_unknown(node.right)
        return self.backend.t_eq(left_expr, right_expr, left_unknown, right_unknown)

    def t_ne(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions:
        """Ternary inequality: UNKNOWN if either operand is UNKNOWN."""
        left_expr, left_unknown = self._to_native_with_unknown(node.left)
        right_expr, right_unknown = self._to_native_with_unknown(node.right)
        return self.backend.t_ne(left_expr, right_expr, left_unknown, right_unknown)

    def t_gt(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions:
        """Ternary greater-than: UNKNOWN if either operand is UNKNOWN."""
        left_expr, left_unknown = self._to_native_with_unknown(node.left)
        right_expr, right_unknown = self._to_native_with_unknown(node.right)
        return self.backend.t_gt(left_expr, right_expr, left_unknown, right_unknown)

    def t_lt(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions:
        """Ternary less-than: UNKNOWN if either operand is UNKNOWN."""
        left_expr, left_unknown = self._to_native_with_unknown(node.left)
        right_expr, right_unknown = self._to_native_with_unknown(node.right)
        return self.backend.t_lt(left_expr, right_expr, left_unknown, right_unknown)

    def t_ge(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions:
        """Ternary greater-than-or-equal: UNKNOWN if either operand is UNKNOWN."""
        left_expr, left_unknown = self._to_native_with_unknown(node.left)
        right_expr, right_unknown = self._to_native_with_unknown(node.right)
        return self.backend.t_ge(left_expr, right_expr, left_unknown, right_unknown)

    def t_le(self, node: TernaryComparisonExpressionNode) -> SupportedExpressions:
        """Ternary less-than-or-equal: UNKNOWN if either operand is UNKNOWN."""
        left_expr, left_unknown = self._to_native_with_unknown(node.left)
        right_expr, right_unknown = self._to_native_with_unknown(node.right)
        return self.backend.t_le(left_expr, right_expr, left_unknown, right_unknown)

    def t_is_in(self, node: TernaryCollectionExpressionNode) -> SupportedExpressions:
        """Ternary membership test: UNKNOWN if element is UNKNOWN."""
        element_expr, unknown_values = self._to_native_with_unknown(node.element)

        # Get the collection
        if isinstance(node.container, (list, tuple, set)):
            collection_list = list(node.container)
        else:
            collection_list = [node.container]

        return self.backend.t_is_in(element_expr, collection_list, unknown_values)

    def t_is_not_in(self, node: TernaryCollectionExpressionNode) -> SupportedExpressions:
        """Ternary non-membership test: UNKNOWN if element is UNKNOWN."""
        element_expr, unknown_values = self._to_native_with_unknown(node.element)

        # Get the collection
        if isinstance(node.container, (list, tuple, set)):
            collection_list = list(node.container)
        else:
            collection_list = [node.container]

        return self.backend.t_is_not_in(element_expr, collection_list, unknown_values)

    # ========================================
    # Logical Operations (min/max semantics)
    # ========================================

    def t_and(self, node: TernaryIterableExpressionNode) -> SupportedExpressions:
        """
        Ternary AND: minimum of operands.

        Truth table:
        T AND T = T (1)
        T AND U = U (0)
        T AND F = F (-1)
        U AND U = U (0)
        U AND F = F (-1)
        F AND F = F (-1)
        """
        if not isinstance(node, TernaryIterableExpressionNode):
            raise TypeError(f"Expected TernaryIterableExpressionNode, got {type(node)}")

        expr_list = [
            ExpressionParameter(operand, expression_system=self.backend).to_native_expression()
            for operand in node.operands
        ]

        # Chain with backend t_and operator using reduce
        return reduce(lambda x, y: self.backend.t_and(x, y), expr_list)

    def t_or(self, node: TernaryIterableExpressionNode) -> SupportedExpressions:
        """
        Ternary OR: maximum of operands.

        Truth table:
        T OR T = T (1)
        T OR U = T (1)
        T OR F = T (1)
        U OR U = U (0)
        U OR F = U (0)
        F OR F = F (-1)
        """
        if not isinstance(node, TernaryIterableExpressionNode):
            raise TypeError(f"Expected TernaryIterableExpressionNode, got {type(node)}")

        expr_list = [
            ExpressionParameter(operand, expression_system=self.backend).to_native_expression()
            for operand in node.operands
        ]

        # Chain with backend t_or operator using reduce
        return reduce(lambda x, y: self.backend.t_or(x, y), expr_list)

    def t_not(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """
        Ternary NOT: sign flip, UNKNOWN stays UNKNOWN.

        Truth table:
        NOT T = F (-1)
        NOT U = U (0)
        NOT F = T (1)
        """
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.t_not(operand_expr)

    def t_xor(self, node: TernaryIterableExpressionNode) -> SupportedExpressions:
        """
        Ternary XOR: exactly one TRUE.

        Returns TRUE if exactly one operand is TRUE and no operands are UNKNOWN.
        Returns UNKNOWN if any operand is UNKNOWN.
        Returns FALSE otherwise.
        """
        if not isinstance(node, TernaryIterableExpressionNode):
            raise TypeError(f"Expected TernaryIterableExpressionNode, got {type(node)}")

        expr_list = [
            ExpressionParameter(operand, expression_system=self.backend).to_native_expression()
            for operand in node.operands
        ]

        # Chain with backend t_xor operator using reduce
        return reduce(lambda x, y: self.backend.t_xor(x, y), expr_list)

    def t_xor_parity(self, node: TernaryIterableExpressionNode) -> SupportedExpressions:
        """
        Ternary XOR parity: odd number of TRUEs.

        Returns TRUE if odd number of operands are TRUE and no operands are UNKNOWN.
        Returns UNKNOWN if any operand is UNKNOWN.
        Returns FALSE otherwise.
        """
        if not isinstance(node, TernaryIterableExpressionNode):
            raise TypeError(f"Expected TernaryIterableExpressionNode, got {type(node)}")

        expr_list = [
            ExpressionParameter(operand, expression_system=self.backend).to_native_expression()
            for operand in node.operands
        ]

        # Chain with backend t_xor_parity operator using reduce
        return reduce(lambda x, y: self.backend.t_xor_parity(x, y), expr_list)

    # ========================================
    # Constants
    # ========================================

    def always_true(self, node: TernaryConstantExpressionNode) -> SupportedExpressions:
        """Return constant TRUE (1)."""
        return self.backend.always_true_ternary()

    def always_false(self, node: TernaryConstantExpressionNode) -> SupportedExpressions:
        """Return constant FALSE (-1)."""
        return self.backend.always_false_ternary()

    def always_unknown(self, node: TernaryConstantExpressionNode) -> SupportedExpressions:
        """Return constant UNKNOWN (0)."""
        return self.backend.always_unknown()

    # ========================================
    # Conversions (Ternary → Boolean)
    # ========================================

    def is_true(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """Convert ternary to boolean: TRUE(1) → True, else → False."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.is_true_ternary(operand_expr)

    def is_false(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """Convert ternary to boolean: FALSE(-1) → True, else → False."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.is_false_ternary(operand_expr)

    def is_unknown(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """Convert ternary to boolean: UNKNOWN(0) → True, else → False."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.is_unknown(operand_expr)

    def is_known(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """Convert ternary to boolean: TRUE or FALSE → True, UNKNOWN → False."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.is_known(operand_expr)

    def maybe_true(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """Convert ternary to boolean: TRUE or UNKNOWN → True, FALSE → False."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.maybe_true(operand_expr)

    def maybe_false(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """Convert ternary to boolean: FALSE or UNKNOWN → True, TRUE → False."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.maybe_false(operand_expr)

    # ========================================
    # Conversions (Boolean → Ternary)
    # ========================================

    def to_ternary(self, node: TernaryUnaryExpressionNode) -> SupportedExpressions:
        """Convert boolean to ternary: True → 1, False → -1."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.to_ternary(operand_expr)
