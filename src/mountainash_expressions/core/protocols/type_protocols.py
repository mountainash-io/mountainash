
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union
from typing import Protocol
from enum import Enum, auto

# from ibis.expr.visualize import get_type


if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode, TypeExpressionNode, SupportedTypeExpressionNodeTypes
    from ...types import SupportedExpressions
    from ..namespaces import BaseNamespace


class ENUM_TYPE_OPERATORS(Enum):
    """
    Enumeration for type casting operators.
    """
    CAST = auto()


class TypeVisitorProtocol(Protocol):

    def visit_expression_node(self, node: SupportedTypeExpressionNodeTypes) -> SupportedExpressions: ...
    def cast(self, node: TypeExpressionNode) -> SupportedExpressions: ...

class TypeExpressionProtocol(Protocol):
    def cast(self, operand_expr: SupportedExpressions, type: Any, **kwargs) -> SupportedExpressions: ...

class TypeBuilderProtocol(Protocol):
    def cast(self, type: Union[BaseNamespace,ExpressionNode, Any]) -> BaseNamespace: ...
