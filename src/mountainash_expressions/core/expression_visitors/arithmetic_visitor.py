from __future__ import annotations

from typing import Callable, TYPE_CHECKING, Dict
from enum import Enum
from functools import reduce




from ..expression_parameters import ExpressionParameter
from .expression_visitor import ExpressionVisitor


from ..protocols import ENUM_ARITHMETIC_OPERATORS, ArithmeticVisitorProtocol

from ...types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes import (
    ArithmeticExpressionNode,
    ArithmeticIterableExpressionNode,
    SupportedArithmeticExpressionNodeTypes
)


class ArithmeticExpressionVisitor(ExpressionVisitor,
                            ArithmeticVisitorProtocol,#, LiteralOperatorProtocol,
):

    # ========================================
    # Arithmetic Comparison Operations
    # ========================================


    @property
    def _arithmetic_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_ARITHMETIC_OPERATORS.SUBTRACT: self.subtract,
            ENUM_ARITHMETIC_OPERATORS.DIVIDE:   self.divide,
            ENUM_ARITHMETIC_OPERATORS.MODULO:   self.modulo,
            ENUM_ARITHMETIC_OPERATORS.POWER:    self.power,
            ENUM_ARITHMETIC_OPERATORS.FLOOR_DIVIDE:   self.floor_divide,

            ENUM_ARITHMETIC_OPERATORS.ADD:      self.add,
            ENUM_ARITHMETIC_OPERATORS.MULTIPLY: self.multiply,
        }

    # ========================================
    # Boolean Comparison Operations
    # ========================================


    def visit_expression_node(self, node: SupportedArithmeticExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._arithmetic_ops, node)
        return op_func(node)


    # ========================================
    # Arithmetic Operations
    # ========================================


    def subtract(self, node: ArithmeticExpressionNode) -> SupportedExpressions:
        """Create a subtract expression."""

        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr = ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.subtract(left_expr, right_expr)


    def divide(self, node: ArithmeticExpressionNode) -> SupportedExpressions:
        """Create a divide expression."""

        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr = ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.divide(left_expr, right_expr)


    def modulo(self, node: ArithmeticExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr = ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.modulo(left_expr, right_expr)


    def power(self, node: ArithmeticExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr = ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.power(left_expr, right_expr)


    def floor_divide(self, node: ArithmeticExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr = ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.floor_divide(left_expr, right_expr)


    # ========================================
    # Arithmetic Iterable Operations
    # ========================================


    def add(self, node: ArithmeticIterableExpressionNode) -> SupportedExpressions:
        """
        Arithmetic ADD: Sum all operands

        TODO: What to do with failures and NULLS?
        """

        expr_list = [ ExpressionParameter(operand, expression_system=self.backend).to_native_expression() for operand in node.operands ]

        # Chain with backend and_ operator using reduce
        return reduce(lambda x, y: self.backend.add(x, y), expr_list)


    def multiply(self, node: ArithmeticIterableExpressionNode) -> SupportedExpressions:
        """
        Arithmetic MULTIPLY: Multiply all operands
        """

        expr_list = [ ExpressionParameter(operand, expression_system=self.backend).to_native_expression() for operand in node.operands ]

        # Chain with backend and_ operator using reduce
        return reduce(lambda x, y: self.backend.multiply(x, y), expr_list)
