"""Conditional expression nodes.

Pydantic-validated AST nodes for conditional operations.
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING
from pydantic import Field

from .base_expression_node import ExpressionNode
from ..protocols.conditional_protocols import ENUM_CONDITIONAL_OPERATORS

if TYPE_CHECKING:
    from ..expression_visitors.conditional_visitor import ConditionalExpressionVisitor
    from ...types import SupportedExpressions


class BaseConditionalExpressionNode(ExpressionNode):
    """Base class for conditional expression nodes."""

    operator: ENUM_CONDITIONAL_OPERATORS = Field()

    def accept(self, visitor: ConditionalExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> SupportedExpressions:
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)


class ConditionalExpressionNode(BaseConditionalExpressionNode):
    """
    Node representing conditional if-then-else expressions.

    Used for when().then().otherwise() patterns.
    """

    condition: Any = Field()
    consequence: Any = Field()
    alternative: Any = Field()

    def __init__(
        self,
        operator: ENUM_CONDITIONAL_OPERATORS,
        condition: Any,
        consequence: Any,
        alternative: Any,
    ):
        super().__init__(
            operator=operator,
            condition=condition,
            consequence=consequence,
            alternative=alternative,
        )


# Type alias for supported conditional node types
SupportedConditionalExpressionNodeTypes = ConditionalExpressionNode
