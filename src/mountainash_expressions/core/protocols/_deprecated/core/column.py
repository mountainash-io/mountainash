
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from enum import Enum, auto

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS, CONST_EXPRESSION_SOURCE_OPERATORS
from ....types import SupportedExpressions

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode, ColumnExpressionNode
    from ...expression_parameters import ExpressionParameter
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
