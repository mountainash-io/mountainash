from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
# from ibis.expr.types import s  # Removed - not used and causes import error
from pydantic import Field
from .base_expression_node import ExpressionNode


from ..protocols import ENUM_NATIVE_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import NativeExpressionVisitor
    from ...types import SupportedExpressions



class NativeExpressionNode(ExpressionNode):

    operator: ENUM_NATIVE_OPERATORS = Field()
    native_expr: SupportedExpressions = Field()

    def __init__(self, operator: ENUM_NATIVE_OPERATORS, native_expr: SupportedExpressions):
        super().__init__(
            operator=operator,
            native_expr=native_expr
        )


    def accept(self, visitor: NativeExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: NativeExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr
