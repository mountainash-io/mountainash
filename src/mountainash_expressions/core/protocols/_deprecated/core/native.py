
from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Protocol
from enum import Enum, auto
from ....types import SupportedExpressions


if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode, NativeBackendExpressionNode
    from ....types import SupportedExpressions
    from ...expression_builders.base_expression_builder import ExpressionBuilder


class ENUM_NATIVE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    NATIVE = auto()

class NativeVisitorProtocol(Protocol):

    def visit_native_expression(self, expression_node: NativeBackendExpressionNode) -> SupportedExpressions: ...
    def native(self,  expr: ExpressionNode) -> SupportedExpressions: ...

class NativeExpressionProtocol(Protocol):

    def native(self,  expr: ExpressionNode) -> SupportedExpressions: ...

class NativeBuilderProtocol(Protocol):
    def native(self) -> ExpressionBuilder: ...
