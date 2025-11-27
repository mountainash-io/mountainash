from __future__ import annotations
from typing import Any, TYPE_CHECKING
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

    def eval(self, dataframe: Any) -> SupportedExpressions:
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)


class TypeExpressionNode(BaseTypeExpressionNode):

    operand: Any = Field()
    type: Any = Field()

    def __init__(self, operator: ENUM_TYPE_OPERATORS, operand: Any, type):
        super().__init__(operator=operator,
            operand=operand,
            type=type
        )
