"""Conditional expression visitor.

Standalone visitor for conditional operations (if-then-else).
"""

from __future__ import annotations
from typing import Callable, Dict, TYPE_CHECKING
from enum import Enum

from ..expression_parameters import ExpressionParameter
from .expression_visitor import ExpressionVisitor
from ..protocols.conditional_protocols import (
    ENUM_CONDITIONAL_OPERATORS,
    ConditionalVisitorProtocol,
)

if TYPE_CHECKING:
    from ..expression_nodes.conditional_expression_nodes import (
        ConditionalExpressionNode,
        SupportedConditionalExpressionNodeTypes,
    )
    from ...types import SupportedExpressions


class ConditionalExpressionVisitor(ExpressionVisitor, ConditionalVisitorProtocol):
    """Visitor for conditional expression operations."""

    @property
    def _conditional_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_CONDITIONAL_OPERATORS.IF_THEN_ELSE: self.if_then_else,
        }

    def visit_expression_node(
        self, node: SupportedConditionalExpressionNodeTypes
    ) -> SupportedExpressions:
        """Dispatch to appropriate visitor method based on operator."""
        op_func = self._get_expr_op(self._conditional_ops, node)
        return op_func(node)

    def if_then_else(
        self, node: ConditionalExpressionNode
    ) -> SupportedExpressions:
        """
        Process an if-then-else conditional expression.

        Evaluates condition, consequence, and alternative, then delegates
        to the backend's if_then_else method.
        """
        condition_expr = ExpressionParameter(
            node.condition, expression_system=self.backend
        ).to_native_expression()
        consequence_expr = ExpressionParameter(
            node.consequence, expression_system=self.backend
        ).to_native_expression()
        alternative_expr = ExpressionParameter(
            node.alternative, expression_system=self.backend
        ).to_native_expression()

        return self.backend.if_then_else(
            condition_expr, consequence_expr, alternative_expr
        )
