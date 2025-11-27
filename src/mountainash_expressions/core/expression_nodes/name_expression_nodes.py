from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
# from ibis.expr.types import s  # Removed - not used and causes import error
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

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: NameExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


class NameExpressionNode(BaseNameExpressionNode):

    operand: Any = Field()

    def __init__(self, operator: ENUM_NAME_OPERATORS, operand: Any):
        super().__init__(operator=operator,
            operand=operand
        )

class NameAliasExpressionNode(BaseNameExpressionNode):

    operand: Any = Field()
    alias: Any = Field()

    def __init__(self, operator: ENUM_NAME_OPERATORS, operand: Any, alias: Any):
        super().__init__(
            operator=operator,
            operand=operand,
            alias=alias
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
