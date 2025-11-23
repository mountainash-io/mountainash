
from typing import Callable, TYPE_CHECKING, Dict, Any, Literal
from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS


from ..expression_parameters import ExpressionParameter
from ..expression_system.base import ExpressionSystem
from .expression_visitor import ExpressionVisitor


from ..protocols import ENUM_NULL_OPERATORS, NullVisitorProtocol
from ..protocols.null.null_constant import ENUM_NULL_CONSTANT_OPERATORS, NullConstantVisitorProtocol
from ..protocols.null.null_logical import ENUM_NULL_LOGICAL_OPERATORS, NullLogicalVisitorProtocol

from ....types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes.null_expression_nodes import (
    NullExpressionNode,
    NullConstantExpressionNode,
    NullLogicalExpressionNode
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

    def visit_expression_node(self, node: NullExpressionNode) -> SupportedExpressions:
        op_func = self._get_expr_op(self._null_ops, node)
        return op_func(node)


    def visit_null_constant_expression(self, node: NullConstantExpressionNode) -> SupportedExpressions:
        op_func = self._get_expr_op(self._null_constant_ops, node)
        return op_func(node)


    def visit_null_logical_expression(self, node: NullLogicalExpressionNode) -> SupportedExpressions:
        op_func = self._get_expr_op(self._null_logical_ops, node)
        return op_func(node)


    # ========================================
    # Null Operations
    # ========================================


    def is_null(self, node: NullExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.is_null(operand_expr)

    def not_null(self, node: NullExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        is_null_result =  self.backend.is_null(operand_expr)
        return self.backend.not_(is_null_result)

    def always_null(self) -> SupportedExpressions:
        """Create a subtract expression."""
        return self.backend.lit(None)


    def fill_null(self, node: NullExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.fill_null(operand_expr, node.value)

    def null_if(self, node: NullExpressionNode) -> SupportedExpressions:
         """Create a subtract expression."""

         operand_expr =  ExpressionParameter(node.operand).to_native_expression()
         return self.backend.null_if(operand_expr, node.condition)
