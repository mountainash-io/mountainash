from __future__ import annotations
from abc import abstractmethod
from typing import Any, List, Callable, Dict, TYPE_CHECKING

from ...constants import CONST_EXPRESSION_LOGICAL_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor
from ...expression_nodes import ExpressionNode, LogicalExpressionNode, ComparisonExpressionNode, CollectionExpressionNode, UnaryExpressionNode
from ...expression_parameters import ExpressionParameter
from functools import reduce

class BooleanOperatorsExpressionVisitor(ExpressionVisitor):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN



    # ===============
    # Operations Maps
    # ===============

    @property
    def boolean_logical_ops(self) -> Dict[str, Callable]:

        boolean_logical_ops = {
            CONST_EXPRESSION_LOGICAL_OPERATORS.AND:           self._B_and,
            CONST_EXPRESSION_LOGICAL_OPERATORS.OR:            self._B_or,
            CONST_EXPRESSION_LOGICAL_OPERATORS.NOT:           self._B_negate,
            CONST_EXPRESSION_LOGICAL_OPERATORS.XOR_EXCLUSIVE: self._B_xor_exclusive,
            CONST_EXPRESSION_LOGICAL_OPERATORS.XOR_PARITY:    self._B_xor_parity
        }

        return boolean_logical_ops

    # ===============
    # Expression Visitor Methods
    # ===============

    # ===============
    # Logical Expressions
    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Any:

        if not issubclass(type(expression_node), (LogicalExpressionNode)):
            raise TypeError("Expected a LogicalExpressionNode instance")

        operands_resolved_expression_nodes =  [ ExpressionParameter(operand).resolve_to_expression_node() for operand in expression_node.operands ]


        return self._process_logical_expression(expression_node, operands_resolved_expression_nodes)


    def _process_logical_expression(self, expression_node: LogicalExpressionNode,  operands_expression_nodes: List[ExpressionNode]) -> Any:

        if not issubclass(type(expression_node), (LogicalExpressionNode)):
            raise TypeError("Expected a LogicalExpressionNode instance")

        if expression_node.operator not in self.boolean_logical_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_logical_ops[expression_node.operator]
        return op_func(operands_expression_nodes)


    # Logical Operations
    # ===============

    # @abstractmethod
    # def _B_is_true(self, expression_node: LogicalExpressionNode) -> Any:
    #     pass

    # @abstractmethod
    # def _B_is_false(self, expression_node: LogicalExpressionNode) -> Any:
    #     pass


    @abstractmethod
    def _B_and(self, expression_node: LogicalExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_or(self, expression_node: LogicalExpressionNode) -> Any:
        pass


    @abstractmethod
    def _B_negate(self, expression_node: LogicalExpressionNode ) -> Any:
        """Abstract method to combine expressions using a specified function."""
        pass



    @abstractmethod
    def _B_xor_exclusive(self, expression_node: LogicalExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_xor_parity(self, expression_node: LogicalExpressionNode) -> Any:
        pass
