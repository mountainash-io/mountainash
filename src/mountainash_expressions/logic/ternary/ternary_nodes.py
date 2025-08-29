# file: src/mountainash_dataframes/utils/expressions/ternary/base.py



from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional
from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS
from ..core.base_nodes import ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode, ExpressionVisitor

from ..visitor_factory import ExpressionVisitorFactory
from

class TernaryExpressionNode(ExpressionNode):

    logic_type = "ternary"

    @abstractmethod
    def accept(self, visitor: 'ExpressionVisitor') -> Callable:
        pass

    @abstractmethod
    def eval(self) -> Callable:
        pass

    #TODO: We need a VisitorFactory, based upon the type of visitor we want to use.
    # This is a placeholder for the visitor type, which should be defined based on the context

    def eval_is_true(self) -> Callable:
        """Convert ternary result to boolean TRUE check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            logical_node = TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_TRUE, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr

    def eval_is_false(self) -> Callable:
        """Convert ternary result to boolean FALSE check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            logical_node = TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_FALSE, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr

    def eval_is_unknown(self) -> Callable:
        """Convert ternary result to boolean UNKNOWN check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            logical_node = TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_UNKNOWN, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr



    def eval_maybe_true(self) -> Callable:
        """Convert ternary result to boolean TRUE OR UNKNOWN check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            logical_node = TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.MAYBE_TRUE, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr

    def eval_maybe_false(self) -> Callable:
        """Convert ternary result to boolean FALSE OR UNKNOWN check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            logical_node = TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.MAYBE_FALSE, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr

    def eval_is_known(self) -> Callable:
        """Convert ternary result to boolean NOT UNKNOWN check."""

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            logical_node = TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_KNOWN, [self])
            return visitor.visit_logical_expression(logical_node)(table)

        return eval_expr




class TernaryLiteralExpressionNode(TernaryExpressionNode, LiteralExpressionNode):

    def __init__(self, operator: str, value1: Any, value2: Any):
        self.operator = operator
        self.value1 = value1
        self.value2 = value2

    def accept(self, visitor: 'ExpressionVisitor') -> Callable:
        return visitor.visit_literal_expression(self)

    def eval(self) -> Callable:

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            return visitor.visit_literal_expression(self)(table)

        return eval_expr

class TernaryColumnExpressionNode(TernaryExpressionNode, ColumnExpressionNode):
    def __init__(self, operator: str, column: str, value: Any, compare_column: Optional[str] = None):
        self.operator = operator
        self.column = column
        self.value = value
        self.compare_column = compare_column

    def accept(self, visitor: 'ExpressionVisitor') -> Callable:
        return visitor.visit_column_expression(self)

    def eval(self) -> Callable:

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            return visitor.visit_column_expression(self)(table)

        return eval_expr




class TernaryLogicalExpressionNode(TernaryExpressionNode, LogicalExpressionNode):

    def __init__(self, operator: str, operands: List[TernaryExpressionNode]):
        self.operator = operator
        self.operands = operands


    def accept(self, visitor: 'ExpressionVisitor') -> Callable:
        return visitor.visit_logical_expression(self)

    def eval(self) -> Callable:

        def eval_expr(table: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_ternary_visitor(table)
            return visitor.visit_logical_expression(self)(table)

        return eval_expr
