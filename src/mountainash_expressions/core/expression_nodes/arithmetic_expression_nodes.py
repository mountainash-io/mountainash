from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING, Iterable
# from ibis.expr.types import s  # Removed - not used and causes import error
from pydantic import Field
from .base_expression_node import ExpressionNode



from ..protocols import ENUM_ARITHMETIC_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import ArithmeticExpressionVisitor
    from ...types import SupportedExpressions


class BaseArithmeticExpressionNode(ExpressionNode):
    """
    Node representing arithmetic ordered operations (SUBTRACT, DIVIDE, etc.).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    operator: ENUM_ARITHMETIC_OPERATORS = Field()


    def accept(self, visitor: ArithmeticExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: ArithmeticExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


class ArithmeticExpressionNode(BaseArithmeticExpressionNode):
    """
    Node representing arithmetic ordered operations (SUBTRACT, DIVIDE, etc.).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    left : Any = Field()
    right : Any = Field()

    def __init__(self, operator: ENUM_ARITHMETIC_OPERATORS, left: Any, right: Any):
        super().__init__(
            operator=operator,
            left=left,
            right=right
        )


    # def __init__(self, operator: Enum, left: Any, right: Any):
    #     self.operator = operator
    #     self.left = left
    #     self.right = right


class ArithmeticIterableExpressionNode(BaseArithmeticExpressionNode):
    """
    Node representing arithmetic iterable operations (ADD,  MULTIPLY,).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    # TODO: Can an *iterable parameter be passed to pydantic?

    operands: Iterable[Any] = Field()

    def __init__(self, operator: ENUM_ARITHMETIC_OPERATORS, *operands: Any):
        super().__init__(
            operator=operator,
            operands=operands
        )

    # def __init__(self, operator: Enum, *operands: Any):
    #     self.operator = operator
    #     self.operands = operands



# SupportedArithmeticExpressionNodeTypes: TypeAlias = Union[ArithmeticExpressionNode, ArithmeticIterableExpressionNode]
