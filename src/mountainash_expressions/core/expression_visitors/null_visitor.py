from __future__ import annotations

from typing import Callable, TYPE_CHECKING, Dict
from enum import Enum

from ..expression_parameters import ExpressionParameter
from .expression_visitor import ExpressionVisitor
from ..protocols import ENUM_NULL_OPERATORS, NullVisitorProtocol
from ...types import SupportedExpressions

if TYPE_CHECKING:
    from ..expression_nodes import (
        NullExpressionNode,
        NullConstantExpressionNode,
        NullConditionalExpressionNode,
        NullLogicalExpressionNode,
        SupportedNullExpressionNodeTypes
    )


class NullExpressionVisitor(ExpressionVisitor,
                            NullVisitorProtocol,
):

    # ========================================
    # Arithmetic Comparison Operations
    # ========================================

    @property
    def _null_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_NULL_OPERATORS.FILL_NULL:  self.fill_null,
            ENUM_NULL_OPERATORS.NULL_IF:    self.null_if,
            ENUM_NULL_OPERATORS.ALWAYS_NULL:self.always_null,
            ENUM_NULL_OPERATORS.IS_NULL:    self.is_null,
            ENUM_NULL_OPERATORS.NOT_NULL:   self.not_null,
        }

    # ========================================
    # Boolean Comparison Operations
    # ========================================

    def visit_expression_node(self, node: SupportedNullExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._null_ops, node)
        return op_func(node)


    # ========================================
    # Null Operations
    # ========================================


    def is_null(self, node: NullLogicalExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.is_null(operand_expr)

    def not_null(self, node: NullLogicalExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        is_null_result =  self.backend.is_null(operand_expr)
        return self.backend.not_(is_null_result)

    def always_null(self, node: NullConstantExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""
        return self.backend.lit(None)


    def fill_null(self, node: NullExpressionNode) -> SupportedExpressions:
        """Fill null values with a specified value."""

        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        value_expr = ExpressionParameter(node.value, expression_system=self.backend).to_native_expression()
        return self.backend.fill_null(operand_expr, value_expr)

    def null_if(self, node: NullConditionalExpressionNode) -> SupportedExpressions:
        """Return NULL if condition is true, otherwise return the value."""

        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        condition_expr = ExpressionParameter(node.condition, expression_system=self.backend).to_native_expression()
        return self.backend.null_if(operand_expr, condition_expr)
