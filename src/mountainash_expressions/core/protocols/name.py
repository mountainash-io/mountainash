
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any
from typing import Protocol
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from enum import Enum, auto
from typing_extensions import TypeAlias

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS


if TYPE_CHECKING:
    from ...types import SupportedExpressions
    from ..expression_nodes.name import ExpressionNode, NameExpressionNode
    from ..expression_parameters import ExpressionParameter
    from ..expression_builders.base_expression_builder import ExpressionBuilder
    from ...types import SupportedExpressions



class ENUM_NAME_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    ALIAS = auto()
    NAME_PREFIX = auto()
    NAME_SUFFIX = auto()
    NAME_TO_UPPER = auto()
    NAME_TO_LOWER = auto()


class NameVisitorProtocol(Protocol):

    def visit_expression(self, node: NameExpressionNode) -> SupportedExpressions: ...

    def alias(self, node: NameExpressionNode) -> SupportedExpressions: ...
    def prefix(self, node: NameExpressionNode) -> SupportedExpressions: ...
    def suffix(self, node: NameExpressionNode) -> SupportedExpressions: ...
    def to_upper(self, node: NameExpressionNode) -> SupportedExpressions: ...
    def to_lower(self, node: NameExpressionNode) -> SupportedExpressions: ...

class NameExpressionProtocol(Protocol):
    def alias(self, value: str) -> SupportedExpressions: ...
    def prefix(self, value: str) -> SupportedExpressions: ...
    def suffix(self, value: str) -> SupportedExpressions: ...
    def to_upper(self ) -> SupportedExpressions: ...
    def to_lower(self) -> SupportedExpressions: ...

class NameBuilderProtocol(Protocol):
    def alias(self,  type: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
    def prefix(self,  type: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
    def suffix(self,  type: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
    def to_upper(self) -> ExpressionBuilder: ...
    def to_lower(self) -> ExpressionBuilder: ...
