from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field
from .base_expression_node import ExpressionNode
from ..protocols import ENUM_NULL_OPERATORS



if TYPE_CHECKING:
    from ..expression_visitors import NullExpressionVisitor
    from ...types import SupportedExpressions


class BaseNullExpressionNode(ExpressionNode):

    operator: ENUM_NULL_OPERATORS = Field()


    def accept(self, visitor: NullExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> SupportedExpressions:
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)


class NullExpressionNode(BaseNullExpressionNode):
    """
    Node representing Null operations (SUBTRACT, DIVIDE, etc.).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    operand: Any = Field()
    value: Any = Field()


    def __init__(self, operator: ENUM_NULL_OPERATORS, operand: Any, value: Any):
        super().__init__(
            operator=operator,
            operand = operand,
            value=value

        )




class NullConditionalExpressionNode(BaseNullExpressionNode):
    operand: Any = Field()
    condition: Any = Field()

    def __init__(self, operator: ENUM_NULL_OPERATORS, operand: Any, condition: Any):
        super().__init__(
            operator=operator,
            operand = operand,
            condition=condition

        )


class NullConstantExpressionNode(BaseNullExpressionNode):
    def __init__(self, operator: ENUM_NULL_OPERATORS):
        super().__init__(
            operator=operator
        )

class NullLogicalExpressionNode(BaseNullExpressionNode):
    operand: Any = Field()

    def __init__(self, operator: ENUM_NULL_OPERATORS, operand: Any):
        super().__init__(
            operator=operator,
            operand = operand
        )





# SupportedNullExpresionNodeTypes: TypeAlias = Union[NullExpressionNode, NullConditionalExpressionNode, NullConstantExpressionNode, NullLogicalExpressionNode]
