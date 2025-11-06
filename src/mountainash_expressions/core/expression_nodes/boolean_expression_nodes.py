from __future__ import annotations
from abc import abstractmethod
from typing import Any, List, Callable, Optional, TYPE_CHECKING

from .expression_nodes import ExpressionNode, UnaryExpressionNode, LogicalExpressionNode, ComparisonExpressionNode, ConditionalIfElseExpressionNode, CollectionExpressionNode
from ..constants import CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS, CONST_LOGIC_TYPES

if TYPE_CHECKING:
    from ..expression_visitors import ExpressionVisitor, ExpressionVisitorFactory

class BooleanExpressionNode(ExpressionNode):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN


    @abstractmethod
    def accept(self, visitor: "ExpressionVisitor") -> Any:
        pass

    @abstractmethod
    def eval(self) -> Any:
        pass

    def eval_is_true(self, backend) -> Any:
        """Convert ternary result to boolean TRUE check."""

        def eval_expr(backend: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            logical_node = BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS.IS_TRUE, [self])
            return visitor.visit_boolean_logical_expression(logical_node)

        return eval_expr

    def eval_is_false(self) -> Any:
        """Convert ternary result to boolean FALSE check."""

        def eval_expr(backend: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            logical_node = BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS.IS_FALSE, [self])
            return visitor.visit_boolean_logical_expression(logical_node)

        return eval_expr


class BooleanUnaryExpressionNode(UnaryExpressionNode, BooleanExpressionNode):

    def accept(self, visitor: ExpressionVisitor) -> Any:
        return visitor.visit_boolean_unary_expression(self)

    def eval(self) -> Any:

        def eval_expr(backend: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_boolean_unary_expression(self)

        return eval_expr


class BooleanLogicalExpressionNode(LogicalExpressionNode, BooleanExpressionNode):

    def accept(self, visitor: ExpressionVisitor) -> Any:
        return visitor.visit_logical_expression(self)

    def eval(self) -> Any:

        def eval_expr(backend: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_boolean_logical_expression(self)

        return eval_expr


class BooleanComparisonExpressionNode(ComparisonExpressionNode, BooleanExpressionNode):

    def accept(self, visitor: ExpressionVisitor) -> Callable:
        return visitor.visit_boolean_comparison_expression(self)

    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_boolean_comparison_expression(self)

        return eval_expr



class BooleanConditionalIfElseExpressionNode(ConditionalIfElseExpressionNode, BooleanExpressionNode):

    def accept(self, visitor: ExpressionVisitor) -> Callable:
        return visitor.visit_boolean_conditional_ifelse_expression(self)

    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_boolean_conditional_ifelse_expression(self)

        return eval_expr

class BooleanCollectionExpressionNode(CollectionExpressionNode, BooleanExpressionNode):

    def accept(self, visitor: ExpressionVisitor) -> Callable:
        return visitor.visit_boolean_collection_expression(self)

    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> Any:
            visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_boolean_collection_expression(self)

        return eval_expr



# class BooleanExpressionVisitor(ExpressionVisitor):

#     @abstractmethod
#     def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:
#         pass

#     @abstractmethod
#     def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:
#         pass

#     @abstractmethod
#     def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:
#         pass
