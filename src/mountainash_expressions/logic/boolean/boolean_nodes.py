from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional

from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS
from ..core.base_nodes import ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode, ExpressionVisitor
from ..visitor_factory import ExpressionVisitorFactory

class BooleanExpressionNode(ExpressionNode):

    logic_type = "boolean"

    @abstractmethod
    def accept(self, visitor: 'ExpressionVisitor') -> Callable:
        pass

    @abstractmethod
    def eval(self) -> Callable:
        pass

    def eval_is_true(self) -> Callable:
        """Convert ternary result to boolean TRUE check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            logical_node = BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_TRUE, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr

    def eval_is_false(self) -> Callable:
        """Convert ternary result to boolean FALSE check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            logical_node = BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_FALSE, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr

class BooleanLiteralExpressionNode(LiteralExpressionNode, BooleanExpressionNode):


    def __init__(self, operator: str, value1: Any, value2: Optional[Any] = None):
        self.operator = operator
        self.value1 = value1
        self.value2 = value2

    def accept(self, visitor: ExpressionVisitor) -> Callable:
        return visitor.visit_literal_expression(self)

    def eval(self) -> Callable:

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_boolean_visitor(table)
            return visitor.visit_literal_expression(self)(table)

        return eval_expr



class BooleanColumnExpressionNode(ColumnExpressionNode, BooleanExpressionNode):

    def __init__(self, operator: str, column: str, value: Optional[Any] = None, compare_column: Optional[str] = None):
        self.operator = operator
        self.column = column
        self.value = value
        self.compare_column = compare_column

    def accept(self, visitor: ExpressionVisitor) -> Callable:
        return visitor.visit_column_expression(self)


    def eval(self) -> Callable:

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_boolean_visitor(table)
            return visitor.visit_column_expression(self)(table)

        return eval_expr


class BooleanLogicalExpressionNode(LogicalExpressionNode, BooleanExpressionNode):

    def __init__(self, operator: str, operands: List[ExpressionNode]):
        self.operator = operator
        self.operands = operands

    def accept(self, visitor: ExpressionVisitor) -> Callable:
        return visitor.visit_logical_expression(self)


    def eval(self) -> Callable:

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_boolean_visitor(table)
            return visitor.visit_logical_expression(self)(table)

        return eval_expr


class BooleanExpressionVisitor(ExpressionVisitor):

    @abstractmethod
    def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:
        pass

    @abstractmethod
    def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:
        pass

    @abstractmethod
    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:
        pass
