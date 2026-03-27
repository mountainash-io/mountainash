
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union
from typing import Protocol
from enum import Enum, auto
from ...types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode
    from ..expression_nodes import ColumnExpressionNode, LiteralExpressionNode, SupportedCoreExpressionNodeTypes

    # from ...expression_parameters import ExpressionParameter
    from ...types import SupportedExpressions
    from ..namespaces import BaseNamespace



class ENUM_CORE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    COL = auto()
    LIT = auto()


class CoreVisitorProtocol(Protocol):

    def visit_expression_node(self, node: SupportedCoreExpressionNodeTypes) -> SupportedExpressions: ...
    def col(self, node: ColumnExpressionNode) -> SupportedExpressions: ...
    def lit(self, node: LiteralExpressionNode) -> SupportedExpressions: ...



class CoreExpressionProtocol(Protocol):

    def col(self, name: str, **kwargs) -> SupportedExpressions: ...
    def lit(self, value: Any) -> SupportedExpressions: ...


class CoreBuilderProtocol(Protocol):

    def col(self,  name: Union[BaseNamespace,ExpressionNode, Any]) -> BaseNamespace: ...
    def lit(self, value: Union[BaseNamespace,ExpressionNode, Any]) -> BaseNamespace: ...

    # Native expressions can be parameter to other Nodes
    # def native(self) -> BaseNamespace: ...
