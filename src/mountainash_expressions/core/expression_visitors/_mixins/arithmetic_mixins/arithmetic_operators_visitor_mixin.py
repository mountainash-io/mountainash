from __future__ import annotations
from abc import abstractmethod
from typing import Any, Callable, Dict

from ...constants import CONST_EXPRESSION_ARITHMETIC_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor
from ...expression_nodes import ExpressionNode, ArithmeticExpressionNode
from ...expression_parameters import ExpressionParameter


class ArithmeticOperatorsExpressionVisitor(ExpressionVisitor):
    """
    Mixin for handling arithmetic operations.

    This mixin provides the visitor methods for arithmetic expressions
    like ADD, SUBTRACT, MULTIPLY, DIVIDE, etc.
    """

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN

    # ===============
    # Operations Maps
    # ===============

    @property
    def arithmetic_ops(self) -> Dict[str, Callable]:
        """Map arithmetic operators to their implementation methods."""
        return {
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.ADD:           self._add,
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.SUBTRACT:      self._subtract,
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.MULTIPLY:      self._multiply,
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.DIVIDE:        self._divide,
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.MODULO:        self._modulo,
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.POWER:         self._power,
            CONST_EXPRESSION_ARITHMETIC_OPERATORS.FLOOR_DIVIDE:  self._floor_divide,
        }

    # ===============
    # Expression Visitor Methods
    # ===============

    def visit_arithmetic_expression(self, expression_node: ArithmeticExpressionNode) -> Any:
        """
        Visit an arithmetic expression node.

        Args:
            expression_node: The arithmetic expression to visit

        Returns:
            Backend-specific arithmetic expression
        """
        if expression_node.operator not in self.arithmetic_ops:
            raise ValueError(f"Unsupported arithmetic operator: {expression_node.operator}")

        left_parameter = ExpressionParameter(expression_node.left)
        right_parameter = ExpressionParameter(expression_node.right)

        left_resolved = left_parameter.resolve_to_expression_node()
        right_resolved = right_parameter.resolve_to_expression_node()

        return self._process_arithmetic_expression(expression_node, left_resolved, right_resolved)

    def _process_arithmetic_expression(
        self,
        expression_node: ArithmeticExpressionNode,
        left: ExpressionNode,
        right: ExpressionNode
    ) -> Any:
        """
        Process an arithmetic expression with resolved operands.

        Args:
            expression_node: The arithmetic expression
            left: Resolved left operand
            right: Resolved right operand

        Returns:
            Backend-specific arithmetic expression
        """
        if expression_node.operator not in self.arithmetic_ops:
            raise ValueError(f"Unsupported arithmetic operator: {expression_node.operator}")

        op_func = self.arithmetic_ops[expression_node.operator]
        return op_func(left, right)

    # ===============
    # Arithmetic Operations (Abstract Methods)
    # ===============

    @abstractmethod
    def _add(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Addition: left + right"""
        pass

    @abstractmethod
    def _subtract(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Subtraction: left - right"""
        pass

    @abstractmethod
    def _multiply(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Multiplication: left * right"""
        pass

    @abstractmethod
    def _divide(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Division: left / right"""
        pass

    @abstractmethod
    def _modulo(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Modulo: left % right"""
        pass

    @abstractmethod
    def _power(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Exponentiation: left ** right"""
        pass

    @abstractmethod
    def _floor_divide(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        """Floor division: left // right"""
        pass
