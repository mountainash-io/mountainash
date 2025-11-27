from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field
from .base_expression_node import ExpressionNode


from ..protocols import ENUM_CORE_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import CoreExpressionVisitor
    from ...types import SupportedExpressions



class BaseCoreExpressionNode(ExpressionNode):

    operator: ENUM_CORE_OPERATORS = Field()


    def accept(self, visitor: CoreExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> SupportedExpressions:
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)



class ColumnExpressionNode(BaseCoreExpressionNode):


    column: Any = Field()

    def __init__(self, operator: ENUM_CORE_OPERATORS, column: Any):
        super().__init__(
            operator=operator,
            column=column
        )



class LiteralExpressionNode(BaseCoreExpressionNode):
    """
    Literal value expression node.

    Represents a constant literal value (string, number, boolean, etc.).
    """

    value: Any = Field()

    def __init__(self, operator: ENUM_CORE_OPERATORS, value: Any):
        super().__init__(
            operator=operator,
            value=value
        )



# SupportedCoreExpressionNodeTypes: TypeAlias = Union[NativeBackendExpressionNode, ColumnExpressionNode, LiteralExpressionNode]
