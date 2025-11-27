from __future__ import annotations
from typing import Any, TYPE_CHECKING
from typing import Protocol
from enum import Enum, auto

from ....expression_nodes import ExpressionNode
from ....expression_nodes._deprecated.expression_nodes import ConditionalIfElseExpressionNode


if TYPE_CHECKING:
    from .....types import SupportedExpressions
    from ....expression_builders.base_expression_builder import BaseExpressionBuilder as ExpressionBuilder

class ENUM_CONDITIONAL_OPERATORS(Enum):
    """
    Enumeration for conditional operators.

    Attributes:
        - WHEN: Conditional if-then-else expression
        - IF_THEN_ELSE: Conditional if-then-else expression
        - COALESCE: Return first non-null value
        - FILL_NULL: Replace null values with specified value
    """
    WHEN = auto()
    IF_THEN_ELSE = auto()
    COALESCE = auto()
    FILL_NULL = auto()

class ConditionalVisitorProtocol(Protocol):

    def visit_boolean_conditional_expression(self, node: ConditionalIfElseExpressionNode) -> SupportedExpressions: ...

    def when(self, node: ConditionalIfElseExpressionNode) -> SupportedExpressions: ...
    def null_if(self, node: ConditionalIfElseExpressionNode) -> SupportedExpressions: ...
    def if_(self, node: ConditionalIfElseExpressionNode) -> SupportedExpressions: ...


class ConditionalExpressionProtocol(Protocol):

    def when( self, condition: SupportedExpressions, consequence: SupportedExpressions, alternative: SupportedExpressions ) -> Any: ...
    def null_if(self, operand: SupportedExpressions, expr: SupportedExpressions) -> SupportedExpressions: ...
    def if_(self, condition: ExpressionNode, consequence: ExpressionNode, alternative: ExpressionNode) -> SupportedExpressions: ...


class ConditionalBuilderProtocol(Protocol):

    def when( self, condition: SupportedExpressions, consequence: SupportedExpressions, alternative: SupportedExpressions ) -> ExpressionBuilder: ...
    def null_if(self, operand: SupportedExpressions, expr: SupportedExpressions) -> ExpressionBuilder: ...
    def if_(self, condition: ExpressionNode, consequence: ExpressionNode, alternative: ExpressionNode) -> ExpressionBuilder: ...
