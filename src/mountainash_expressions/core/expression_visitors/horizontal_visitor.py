"""
Horizontal operations visitor.

Handles row-wise operations across multiple columns:
- coalesce: first non-null value
- greatest: maximum value
- least: minimum value
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Dict
from enum import Enum
from functools import reduce

from .expression_visitor import ExpressionVisitor
from ..expression_parameters import ExpressionParameter
from ...types import SupportedExpressions
from ..expression_nodes import HorizontalExpressionNode
from ..protocols import HorizontalVisitorProtocol, ENUM_HORIZONTAL_OPERATORS

if TYPE_CHECKING:
    from ..expression_nodes import SupportedHorizontalExpressionNodeTypes


class HorizontalExpressionVisitor(ExpressionVisitor, HorizontalVisitorProtocol):
    """Visitor for horizontal operations across multiple columns."""

    # ===============
    # Operations Maps
    # ===============

    @property
    def _horizontal_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_HORIZONTAL_OPERATORS.COALESCE: self.coalesce,
            ENUM_HORIZONTAL_OPERATORS.GREATEST: self.greatest,
            ENUM_HORIZONTAL_OPERATORS.LEAST:    self.least,
        }

    # ===============
    # Expression Visitor Methods
    # ===============

    def visit_expression_node(self, node: SupportedHorizontalExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._horizontal_ops, node)
        return op_func(node)

    # ===============
    # Horizontal Operations
    # ===============

    def coalesce(self, node: HorizontalExpressionNode) -> SupportedExpressions:
        """Return first non-null value across columns."""
        if not isinstance(node, HorizontalExpressionNode):
            raise TypeError(f"Expected HorizontalExpressionNode, got {type(node)}")

        expr_list = [
            ExpressionParameter(operand, expression_system=self.backend).to_native_expression()
            for operand in node.operands
        ]
        return reduce(lambda x, y: self.backend.coalesce(x, y), expr_list)

    def greatest(self, node: HorizontalExpressionNode) -> SupportedExpressions:
        """Return maximum value across columns."""
        expr_list = [
            ExpressionParameter(operand, expression_system=self.backend).to_native_expression()
            for operand in node.operands
        ]
        return reduce(lambda x, y: self.backend.greatest(x, y), expr_list)

    def least(self, node: HorizontalExpressionNode) -> SupportedExpressions:
        """Return minimum value across columns."""
        expr_list = [
            ExpressionParameter(operand, expression_system=self.backend).to_native_expression()
            for operand in node.operands
        ]
        return reduce(lambda x, y: self.backend.least(x, y), expr_list)
