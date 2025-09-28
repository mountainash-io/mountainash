from abc import abstractmethod
from typing import Any, List, Callable, Dict, TYPE_CHECKING

from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode, LogicalExpressionNode, ComparisonExpressionNode, ConditionalExpressionNode, ArithmeticExpressionNode, CollectionExpressionNode, StringExpressionNode

from functools import reduce

class BooleanExpressionVisitor(ExpressionVisitor):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN



    # ===============
    # Operations Maps
    # ===============
    @property
    def boolean_collection_ops(self) -> Dict[str, Callable]:
        """Abstract method to define boolean comparison operations."""

        boolean_comparison_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.IN:            self._in,
            CONST_EXPRESSION_LOGIC_OPERATORS.NOT_IN:        self._not_in,
        }

        return boolean_comparison_ops





    # ===============
    # Expression Visitor Methods
    # ===============



    # ===============
    # Collection Expression
    def visit_collection_expression(self, expression_node: CollectionExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        element_expression_parameter =  ExpressionParameter(expression_node.element)
        container_expression_parameter = ExpressionParameter(expression_node.container)

        left_resolved_expr = element_expression_parameter.resolve_to_expression_node()
        right_resolved_expr = container_expression_parameter.resolve_to_expression_node()

        return self._process_collection_expression(expression_node, left_resolved_expr, right_resolved_expr)


    def _process_collection_expression(self, expression_node: CollectionExpressionNode, element: ExpressionNode, container: ExpressionNode) -> Any:

        if expression_node.operator not in self.boolean_comparison_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.boolean_comparison_ops[expression_node.operator]
        return op_func(element, container)



    @abstractmethod
    def _B_in(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _B_not_in(self, left: ExpressionNode, right: ExpressionNode) -> Any:
        pass



    # ===============
    # Helper Methods
    # ===============

    # def _combine(self, table: Any, expression_nodes: List["ExpressionNode"], combine_func):
    #     """ Combine multiple expressions using a specified function."""

    #     if not expression_nodes:
    #         raise ValueError("Cannot perform operations on empty operands list")

    #     expressions = [expression_node.accept(self)(table)
    #                     for expression_node in expression_nodes]

    #     # Handle single operand case
    #     if len(expressions) == 1:
    #         return expressions[0]

    #     return reduce(combine_func, expressions)
