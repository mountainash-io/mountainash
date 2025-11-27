
from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Protocol
from enum import Enum, auto

from ....types import SupportedExpressions

if TYPE_CHECKING:
    from ...expression_nodes import ColumnExpressionNode
    from ....types import SupportedExpressions
    from ...expression_builders.base_expression_builder import ExpressionBuilder


class ENUM_COLUMN_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    COL = auto()


class ColumnVisitorProtocol(Protocol):

    def visit_column_expression(self, node: ColumnExpressionNode) -> SupportedExpressions: ...
    def col(self,  node: ColumnExpressionNode) -> SupportedExpressions: ...


class ColumnExpressionProtocol(Protocol):

    def col(self,  column: str, /,  **kwargs) -> SupportedExpressions: ...


class ColumnBuilderProtocol(Protocol):

    def col(self,  column: str, /, **kwargs) -> ExpressionBuilder: ...
