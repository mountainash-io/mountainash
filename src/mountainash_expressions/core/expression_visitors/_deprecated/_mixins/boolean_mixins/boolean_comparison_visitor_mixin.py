from __future__ import annotations
from abc import abstractmethod
from typing import Any, Callable, Dict

from ...constants import CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor
from ...expression_nodes import ExpressionNode, ComparisonExpressionNode
from ...expression_parameters import ExpressionParameter

class BooleanComparisonExpressionVisitor(ExpressionVisitor):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN


    # ===============
    # Comparison Visitor Services Menu
    # ===============

    @property
    def boolean_comparison_ops(self) -> Dict[str, Callable]:
        """Abstract method to define boolean comparison operations."""

        boolean_comparison_ops = {
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.EQ:            self._B_eq,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.NE:            self._B_ne,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.GT:            self._B_gt,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.LT:            self._B_lt,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.GE:            self._B_ge,
            CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.LE:            self._B_le,
            # CONST_EXPRESSION_LOGICAL_COMPARISON_OPERATORS.BETWEEN:            self._B_le,
        }

        return boolean_comparison_ops


    # ===============
    # Comparison Visitor Front Door
    # ===============
    def visit_comparison_expression(self, expression_node: ComparisonExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        left_expression_parameter =  ExpressionParameter(expression_node.left)
        right_expression_parameter = ExpressionParameter(expression_node.right)

        left_resolved_expr = left_expression_parameter.resolve_to_expression_node()
        right_resolved_expr = right_expression_parameter.resolve_to_expression_node()

        return self._process_comparison_expression(expression_node, left_resolved_expr, right_resolved_expr)


    def _process_comparison_expression(self, expression_node: ComparisonExpressionNode, left: ExpressionNode, right: ExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}" )

        visitor_operator = self.boolean_comparison_ops[expression_node.operator]
        return visitor_operator(left, right)


    # ===============
    # Comparison Back of House Operations
    # ===============

    @abstractmethod
    def _B_eq(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_ne(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_gt(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_lt(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_ge(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_le(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        pass
