
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from typing import Protocol
from enum import Enum, auto
from ....types import SupportedExpressions


if TYPE_CHECKING:
    from ...expression_nodes import LiteralExpressionNode
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
