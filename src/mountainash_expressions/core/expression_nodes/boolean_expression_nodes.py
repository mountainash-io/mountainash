from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING, Iterable
from pydantic import Field

from .base_expression_node import ExpressionNode
from ...constants import CONST_LOGIC_TYPES

from ..protocols import ENUM_BOOLEAN_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import ExpressionVisitorFactory
    from ..expression_visitors.boolean_visitor import BooleanExpressionVisitor

    from ...types import SupportedExpressions





class BooleanExpressionNode(ExpressionNode):

    operator: ENUM_BOOLEAN_OPERATORS = Field()

    logic_type: CONST_LOGIC_TYPES = Field(default=CONST_LOGIC_TYPES.BOOLEAN)


    def accept(self, visitor: BooleanExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:

        def eval_expr(backend: Any) -> SupportedExpressions:
            visitor: BooleanExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)

        return eval_expr


    def eval_is_true(self) -> Callable:
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

    operand: Any = Field()

    def __init__(self, operator: ENUM_BOOLEAN_OPERATORS, operand: Any):
        super().__init__(
            operator=operator,
            operand=operand
        )



class BooleanIterableExpressionNode(BooleanExpressionNode):

    operands: Iterable[Any] = Field()

    def __init__(self, operator: ENUM_BOOLEAN_OPERATORS, *operands: Any):
        super().__init__(
            operator=operator,
            operands=operands
        )



class BooleanComparisonExpressionNode(BooleanExpressionNode):

    left: Any = Field()
    right: Any = Field()

    def __init__(self, operator: ENUM_BOOLEAN_OPERATORS, left: Any, right: Any):
        super().__init__(
            operator=operator,
            left=left,
            right=right
        )




class BooleanBetweenExpressionNode(BooleanExpressionNode):
    left: Any = Field()
    right: Any = Field()
    closed: Any = Field()

    def __init__(self, operator: ENUM_BOOLEAN_OPERATORS, left: Any, right: Any, closed: Any):
        super().__init__(operator=operator,
            left = left,
            right = right,
            closed = closed

        )


class BooleanIsCloseExpressionNode(BooleanExpressionNode):
    left: Any = Field()
    right: Any = Field()
    precision: Any = Field()

    def __init__(self, operator: ENUM_BOOLEAN_OPERATORS, left: Any, right: Any, precision: Any):
        super().__init__(operator=operator,
            left = left,
            right = right,
            precision = precision
        )



class BooleanCollectionExpressionNode(BooleanExpressionNode):

    operand: Any = Field()
    element: Any = Field()
    container: Any = Field()

    def __init__(self, operator: ENUM_BOOLEAN_OPERATORS, operand: Any, element: Any, container: Any):
        super().__init__(operator=operator,
            operand = operand,
            element = element,
            container = container
        )


class BooleanConstantExpressionNode(BooleanExpressionNode):
    def __init__(self, operator: ENUM_BOOLEAN_OPERATORS):
        super().__init__(operator=operator)




# class BooleanConditionalIfElseExpressionNode(ConditionalIfElseExpressionNode, BooleanExpressionNode):

#     def accept(self, visitor: ExpressionVisitor) -> Callable:
#         return visitor.visit_boolean_conditional_ifelse_expression(self)

#     def eval(self) -> Callable:

#         def eval_expr(backend: Any) -> Any:
#             visitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
#             return visitor.visit_boolean_conditional_ifelse_expression(self)

#         return eval_expr


# SupportedBooleanExpressionNodeTypes: TypeAlias = Union[BooleanComparisonExpressionNode, BooleanCollectionExpressionNode, BooleanConstantExpressionNode, BooleanIterableExpressionNode, BooleanUnaryExpressionNode]
