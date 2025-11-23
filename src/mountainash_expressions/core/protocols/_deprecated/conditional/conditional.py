from __future__ import annotations
from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from typing import Protocol, runtime_checkable
from enum import Enum, auto

from ...constants import CONST_EXPRESSION_CONDITIONAL_OPERATORS, CONST_LOGIC_TYPES
from ...expression_nodes import ExpressionNode, ConditionalIfElseExpressionNode
from ...expression_builders.base_expression_builder import ExpressionBuilder


if TYPE_CHECKING:
    from ....types import SupportedExpressions

class ENUM_CONDITIONAL_OPERATORS(Enum):
    """
    Enumeration for conditional operators.

    Attributes:
        - WHEN: Conditional if-then-else expression
        - COALESCE: Return first non-null value
        - FILL_NULL: Replace null values with specified value
    """
    WHEN = auto()
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
