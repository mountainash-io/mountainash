from __future__ import annotations
from abc import abstractmethod
from enum import Enum
from typing import Any, List, Callable, Optional, TYPE_CHECKING, Union
from typing_extensions import TypeAlias

from .base_expression_node import ExpressionNode
# UnaryExpressionNode, LogicalExpressionNode, ComparisonExpressionNode, ConditionalIfElseExpressionNode, CollectionExpressionNode
from ...constants import CONST_LOGIC_TYPES

if TYPE_CHECKING:
    from ..expression_visitors import ExpressionVisitor, ExpressionVisitorFactory
    from ..expression_visitors.boolean_visitor import BooleanExpressionVisitor
    from ..protocols import ENUM_BOOLEAN_OPERATORS
    from ...types import SupportedExpressions





class BooleanExpressionNode(ExpressionNode):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN


    @abstractmethod
    def accept(self, visitor: ExpressionVisitor) -> SupportedExpressions:
        pass

    @abstractmethod
    def eval(self) -> SupportedExpressions:
        pass

    def eval_is_true(self, backend) -> Callable:
        """Convert ternary result to boolean TRUE check."""

        def eval_expr(backend: Any) -> SupportedExpressions:
            visitor: BooleanExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            logical_node = BooleanUnaryExpressionNode(ENUM_BOOLEAN_OPERATORS.IS_TRUE, [self])
            return visitor.visit_expression_node(logical_node)

        return eval_expr

    def eval_is_false(self) -> Callable:
        """Convert ternary result to boolean FALSE check."""

        def eval_expr(backend: Any) -> SupportedExpressions:
            visitor: BooleanExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            logical_node = BooleanUnaryExpressionNode(ENUM_BOOLEAN_OPERATORS.IS_FALSE, [self])
            return visitor.visit_expression_node(logical_node)

        return eval_expr


class BooleanUnaryExpressionNode(BooleanExpressionNode):

    def __init__(self, operator: Enum, operand: Any):
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: BooleanExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> SupportedExpressions:
            visitor: BooleanExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)

        return eval_expr


class BooleanIterableExpressionNode(BooleanExpressionNode):

    def __init__(self, operator: Enum, *operands: Any):
        self.operator = operator
        self.operands = operands


    def accept(self, visitor: BooleanExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> SupportedExpressions:
            visitor: BooleanExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)

        return eval_expr


class BooleanComparisonExpressionNode(BooleanExpressionNode):

    def __init__(self, operator: Enum, left: Any, right: Any, closed: Optional[str] = None, precision: Optional[float] = None):

        self.operator = operator
        self.left = left
        self.right = right

        #Parameters for between and is_close
        self.closed = closed
        self.precision = precision


    def accept(self, visitor: BooleanExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> SupportedExpressions:
            visitor: BooleanExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)

        return eval_expr


class BooleanCollectionExpressionNode(BooleanExpressionNode):

    def __init__(self, operator: Enum, element: Any, container: Any ):
        self.operator = operator
        self.element = element
        self.container = container

    def accept(self, visitor: BooleanExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> SupportedExpressions:
            visitor: BooleanExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)

        return eval_expr


class BooleanConstantExpressionNode(BooleanExpressionNode):

    def __init__(self, operator: Enum, element: Any, container: Any ):
        self.operator = operator

    def accept(self, visitor: BooleanExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)


    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> SupportedExpressions:
            visitor: BooleanExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)

        return eval_expr




# class BooleanConditionalIfElseExpressionNode(ConditionalIfElseExpressionNode, BooleanExpressionNode):

#     def accept(self, visitor: ExpressionVisitor) -> Callable:
#         return visitor.visit_boolean_conditional_ifelse_expression(self)

#     def eval(self) -> Callable:

#         def eval_expr(backend: Any) -> Any:
#             visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
#             return visitor.visit_boolean_conditional_ifelse_expression(self)

#         return eval_expr


SupportedBooleanExpressionNodeTypes: TypeAlias = Union[BooleanComparisonExpressionNode, BooleanCollectionExpressionNode, BooleanConstantExpressionNode, BooleanIterableExpressionNode, BooleanUnaryExpressionNode]
