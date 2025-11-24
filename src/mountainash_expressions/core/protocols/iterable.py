
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any, Iterable, Union
from typing import Protocol, runtime_checkable
from enum import Enum, auto
from abc import ABC, abstractmethod
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode, IterableExpressionNode, SupportedIterableExpressionNodeTypes
    from ..expression_parameters import ExpressionParameter
    from ...types import SupportedExpressions
    from ..expression_builders.base_expression_builder import ExpressionBuilder


validArithmeticExpresionNodes: TypeAlias = IterableExpressionNode

class ENUM_ITERABLE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    COALESCE = auto()
    GREATEST = auto()
    LEAST = auto()

class IterableVisitorProtocol(Protocol):

    def visit_expression_node(self, node: SupportedIterableExpressionNodeTypes) -> SupportedExpressions: ...

    def coalesce(self, node: IterableExpressionNode) -> SupportedExpressions: ...
    def greatest(self, node: IterableExpressionNode) -> SupportedExpressions: ...
    def least(self,    node: IterableExpressionNode) -> SupportedExpressions: ...



class IterableExpressionProtocol(Protocol):

    def coalesce(self, *operands: SupportedExpressions) -> SupportedExpressions: ...
    def greatest(self, *operands: SupportedExpressions) -> SupportedExpressions: ...
    def least(self,    *operands: SupportedExpressions) -> SupportedExpressions: ...

class IterableBuilderProtocol(Protocol):

    def coalesce(self, *other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
    def greatest(self, *other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
    def least(self,    *other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
