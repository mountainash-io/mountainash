from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional

from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_EXPRESSION_LOGIC_TYPES
from ..core.base_nodes import ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode
from ...visitors.core import ExpressionVisitor,Visitor
from ...helpers.visitor_factory import ExpressionVisitorFactory

class BooleanExpressionNode(ExpressionNode):


    @property
    def _logic_type(self) -> str:
        return CONST_EXPRESSION_LOGIC_TYPES.BOOLEAN


    @abstractmethod
    def accept(self, visitor: ExpressionVisitor) -> Callable:
        pass

    @abstractmethod
    def eval(self) -> Callable:
        pass

    def eval_is_true(self) -> Callable:
        """Convert ternary result to boolean TRUE check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.create_visitor_for_backend(table, self.logic_type)
            logical_node = BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_TRUE, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr

    def eval_is_false(self) -> Callable:
        """Convert ternary result to boolean FALSE check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.create_visitor_for_backend(table, self.logic_type)
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
            visitor = ExpressionVisitorFactory.create_visitor_for_backend(table, self.logic_type)
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
            visitor = ExpressionVisitorFactory.create_visitor_for_backend(table, self.logic_type)
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
            visitor = ExpressionVisitorFactory.create_visitor_for_backend(table, self.logic_type)
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
