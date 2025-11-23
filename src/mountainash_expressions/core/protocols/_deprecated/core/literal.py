
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from enum import Enum, auto
from ....types import SupportedExpressions

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS, CONST_EXPRESSION_LITERAL_OPERATORS
from ...expression_parameters import ExpressionParameter

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode, LiteralExpressionNode
    from ....types import SupportedExpressions
    from ...expression_builders.base_expression_builder import ExpressionBuilder



class ENUM_LITERAL_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    LIT = auto()

class LiteralVisitorProtocol(Protocol):

    def visit_literal_expression(self, node: LiteralExpressionNode) -> SupportedExpressions: ...
    def lit(self, node: LiteralExpressionNode) -> SupportedExpressions: ...

class LiteralExpressionProtocol(Protocol):
    def lit(self, value: Any) -> SupportedExpressions: ...

class LiteralBuilderProtocol(Protocol):
    def lit(self, value: Any) -> ExpressionBuilder: ...
