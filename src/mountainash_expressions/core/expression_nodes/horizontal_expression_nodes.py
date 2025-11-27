from __future__ import annotations
from typing import Any, TYPE_CHECKING, Iterable
from pydantic import Field
from .base_expression_node import ExpressionNode


from ..protocols import ENUM_HORIZONTAL_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import HorizontalExpressionVisitor
    from ...types import SupportedExpressions


class BaseHorizontalExpressionNode(ExpressionNode):
    """
    Base node for horizontal operations (coalesce, greatest, least).

    Horizontal operations work row-wise across multiple columns,
    returning a single value per row from the input columns.
    """

    operator: ENUM_HORIZONTAL_OPERATORS = Field()

    def accept(self, visitor: HorizontalExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> SupportedExpressions:
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)


class HorizontalExpressionNode(BaseHorizontalExpressionNode):
    """
    Node for horizontal operations across multiple columns.

    Examples:
        - coalesce(col_a, col_b, col_c) - first non-null value
        - greatest(col_a, col_b, col_c) - maximum value
        - least(col_a, col_b, col_c) - minimum value
    """

    operands: Iterable[Any] = Field()

    def __init__(self, operator: ENUM_HORIZONTAL_OPERATORS, *operands: Any):
        super().__init__(
            operator=operator,
            operands=operands
        )
