from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field
from .base_expression_node import ExpressionNode


from ..protocols import ENUM_NAME_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import NameExpressionVisitor
    from ...types import SupportedExpressions




class BaseNameExpressionNode(ExpressionNode):

    operator: ENUM_NAME_OPERATORS = Field()

    def accept(self, visitor: NameExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> SupportedExpressions:
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)


class NameExpressionNode(BaseNameExpressionNode):

    operand: Any = Field()

    def __init__(self, operator: ENUM_NAME_OPERATORS, operand: Any):
        super().__init__(operator=operator,
            operand=operand
        )

class NameAliasExpressionNode(BaseNameExpressionNode):

    operand: Any = Field()
    name: Any = Field()

    def __init__(self, operator: ENUM_NAME_OPERATORS, operand: Any, name: Any):
        super().__init__(
            operator=operator,
            operand=operand,
            name=name
        )

class NamePrefixExpressionNode(BaseNameExpressionNode):

    operand: Any = Field()
    prefix: Any = Field()

    def __init__(self, operator: ENUM_NAME_OPERATORS, operand: Any, prefix: Any):
        super().__init__(
            operator=operator,
            operand=operand,
            prefix=prefix
        )

class NameSuffixExpressionNode(BaseNameExpressionNode):

    operand: Any = Field()
    suffix: Any = Field()

    def __init__(self, operator: ENUM_NAME_OPERATORS, operand: Any, suffix: Any):
        super().__init__(
            operator=operator,
            operand=operand,
            suffix=suffix
        )
