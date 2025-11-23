
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any, Iterable, Union
from typing import Protocol, runtime_checkable
from enum import Enum, auto
from abc import ABC, abstractmethod
from ...types import SupportedExpressions
from typing_extensions import TypeAlias

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS, CONST_EXPRESSION_NATIVE_OPERATORS

if TYPE_CHECKING:
    from ..expression_nodes.iterable import ExpressionNode, IterableExpressionNode
    from ..expression_parameters import ExpressionParameter
    from ...types import SupportedExpressions
    from ..expression_builders.base_expression_builder import ExpressionBuilder


validArithmeticExpresionNodes: TypeAlias = IterableExpressionNode

class ENUM_CORE_ITERABLE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    COALESCE = auto()
    GREATEST = auto()
    LEAST = auto()

class IterableVisitorProtocol(Protocol):

    def visit_core_iterable_expression(self, node: IterableExpressionNode) -> SupportedExpressions: ...

    def coalesce(self, node: IterableExpressionNode) -> SupportedExpressions: ...
    def greatest(self, node: IterableExpressionNode) -> SupportedExpressions: ...
    def least(self,    node: IterableExpressionNode) -> SupportedExpressions: ...



class IterableExpressionProtocol(Protocol):

    def coalesce(self, *operand_exprs: SupportedExpressions) -> SupportedExpressions: ...
    def greatest(self, *operand_exprs: SupportedExpressions) -> SupportedExpressions: ...
    def least(self,    *operand_exprs: SupportedExpressions) -> SupportedExpressions: ...

class IterableBuilderProtocol(Protocol):

    def coalesce(self, *other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
    def greatest(self, *other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
    def least(self,    *other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
