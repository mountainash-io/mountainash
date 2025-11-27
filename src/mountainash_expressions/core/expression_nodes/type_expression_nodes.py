from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
# from ibis.expr.types import s  # Removed - not used and causes import error
from pydantic import Field
from .base_expression_node import ExpressionNode


from ..protocols import ENUM_TYPE_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import TypeExpressionVisitor
    from ...types import SupportedExpressions




class BaseTypeExpressionNode(ExpressionNode):

    operator: ENUM_TYPE_OPERATORS = Field()


    def accept(self, visitor: TypeExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: TypeExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


class TypeExpressionNode(BaseTypeExpressionNode):

    operand: Any = Field()
    type: Any = Field()

    def __init__(self, operator: ENUM_TYPE_OPERATORS, operand: Any, type):
        super().__init__(operator=operator,
            operand=operand,
            type=type
        )
