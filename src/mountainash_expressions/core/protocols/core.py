
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any, Iterable, Union
from typing import Protocol, runtime_checkable
from enum import Enum, auto
from abc import ABC, abstractmethod
from ...types import SupportedExpressions
from typing_extensions import TypeAlias

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS, CONST_EXPRESSION_NATIVE_OPERATORS

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode
    from ..expression_nodes.core.core_expression_nodes import ColumnExpressionNode, LiteralExpressionNode, NativeBackendExpressionNode

    # from ...expression_parameters import ExpressionParameter
    from ...types import SupportedExpressions
    from ..expression_builders.base_expression_builder import ExpressionBuilder



validArithmeticExpresionNodes: TypeAlias = Union[ColumnExpressionNode, LiteralExpressionNode, NativeBackendExpressionNode]


class ENUM_CORE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    COL = auto()
    LIT = auto()
    NATIVE = auto()


class CoreVisitorProtocol(Protocol):

    def visit_column_expression(self, node: ColumnExpressionNode) -> SupportedExpressions: ...
    def col(self,  node: ColumnExpressionNode) -> SupportedExpressions: ...

    def visit_literal_expression(self, node: LiteralExpressionNode) -> SupportedExpressions: ...
    def lit(self, node: LiteralExpressionNode) -> SupportedExpressions: ...

    def visit_native_expression(self, expression_node: NativeBackendExpressionNode) -> SupportedExpressions: ...
    def native(self,  node: NativeBackendExpressionNode) -> SupportedExpressions: ...


class CoreExpressionProtocol(Protocol):

    def col(self,   column: str, /,  **kwargs) -> SupportedExpressions: ...
    def lit(self,   value: Any) -> SupportedExpressions: ...
    def native(self,  expr: SupportedExpressions) -> SupportedExpressions: ...


class CoreBuilderProtocol(Protocol):

    def col(self,  column: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
    def lit(self, value: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...

    # Native expressions can be parameter to other Nodes
    # def native(self) -> ExpressionBuilder: ...
