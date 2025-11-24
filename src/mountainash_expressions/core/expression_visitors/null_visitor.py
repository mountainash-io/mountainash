
from typing import Callable, TYPE_CHECKING, Dict, Any, Literal
from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS




if TYPE_CHECKING:
    from ..expression_nodes import (
        NullExpressionNode,
        NullConstantExpressionNode,
        NullConditionalExpressionNode,
        NullLogicalExpressionNode,
    SupportedNullExpressionNodeTypes
    )
    from ..expression_parameters import ExpressionParameter
    from ..expression_system.base import ExpressionSystem
    from .expression_visitor import ExpressionVisitor
    from ..protocols import ENUM_NULL_OPERATORS, NullVisitorProtocol
    from ...types import SupportedExpressions


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

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.is_null(operand_expr)

    def not_null(self, node: NullLogicalExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        is_null_result =  self.backend.is_null(operand_expr)
        return self.backend.not_(is_null_result)

    def always_null(self, node: NullConstantExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""
        return self.backend.lit(None)


    def fill_null(self, node: NullExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.fill_null(operand_expr, node.value)

    def null_if(self, node: NullConditionalExpressionNode) -> SupportedExpressions:
         """Create a subtract expression."""

         operand_expr =  ExpressionParameter(node.operand).to_native_expression()
         return self.backend.null_if(operand_expr, node.condition)
