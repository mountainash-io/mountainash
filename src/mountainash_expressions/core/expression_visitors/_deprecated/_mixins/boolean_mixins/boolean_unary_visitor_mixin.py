from __future__ import annotations
from abc import abstractmethod
from typing import Any, List, Callable, Dict

from ...constants import CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS, CONST_EXPRESSION_SOURCE_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor
from ...expression_nodes import ExpressionNode
from ...expression_parameters import ExpressionParameter
from functools import reduce

class BooleanUnaryExpressionVisitor(ExpressionVisitor):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN



    # ===============
    # Operations Maps
    # ===============



    @property
    def boolean_unary_ops(self) -> Dict[str, Callable]:
        boolean_unary_ops = {
            CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS.IS_TRUE:       self._B_is_true,
            CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS.IS_FALSE:      self._B_is_false,
            CONST_EXPRESSION_SOURCE_OPERATORS.IS_NULL:              self._B_is_null,
            CONST_EXPRESSION_SOURCE_OPERATORS.IS_NOT_NULL:          self._B_not_null,
        }

        return boolean_unary_ops



    # ===============
    # Expression Visitor Methods
    # ===============

    # ===============
    # Unary Expressions
    def visit_unary_expression(self, expression_node: LogicalUnaryExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_unary_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        operand_parameter =  ExpressionParameter(expression_node.operand)
        operand_expression_node = operand_parameter.resolve_to_expression_node()

        return self._process_unary_expression(expression_node, operand_expression_node)


    def _process_unary_expression(self, expression_node: LogicalUnaryExpressionNode, operand_expression_node: ExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_unary_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_unary_ops[expression_node.operator]
        return op_func(operand_expression_node)



    # Logical Operations
    # ===============



    # Unary Operations
    # ===============

    @abstractmethod
    def _B_is_null(self, LHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_not_null(self, LHS: ExpressionNode) -> Any:
        pass


    @abstractmethod
    def _B_is_true(self, expression_node: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_is_false(self, expression_node: ExpressionNode) -> Any:
        pass



    # ===============
    # Helper Methods
    # ===============

    def _combine(self, table: Any, expression_nodes: List["ExpressionNode"], combine_func):
        """ Combine multiple expressions using a specified function."""

        if not expression_nodes:
            raise ValueError("Cannot perform operations on empty operands list")

        expressions = [expression_node.accept(self)(table)
                        for expression_node in expression_nodes]

        # Handle single operand case
        if len(expressions) == 1:
            return expressions[0]

        return reduce(combine_func, expressions)
