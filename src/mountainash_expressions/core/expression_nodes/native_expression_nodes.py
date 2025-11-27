from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field
from .base_expression_node import ExpressionNode


from ..protocols import ENUM_NATIVE_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import NativeExpressionVisitor
    from ...types import SupportedExpressions



class NativeExpressionNode(ExpressionNode):
    """Node that wraps a backend-native expression for passthrough.

    The native_expr field uses Any since it can hold any backend-native
    expression type (pl.Expr, nw.Expr, ir.Expr, etc.). The type is validated
    at runtime when the expression is compiled against a specific backend.
    """

    operator: ENUM_NATIVE_OPERATORS = Field()
    native_expr: Any = Field()  # Any backend-native expression type

    def __init__(self, operator: ENUM_NATIVE_OPERATORS, native_expr: SupportedExpressions):
        super().__init__(
            operator=operator,
            native_expr=native_expr
        )


    def accept(self, visitor: NativeExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> SupportedExpressions:
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)
