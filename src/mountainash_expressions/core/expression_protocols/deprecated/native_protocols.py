
from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Protocol
from enum import Enum, auto

if TYPE_CHECKING:
    from ..expression_nodes import NativeExpressionNode
    from ..namespaces import BaseNamespace

    # from ...expression_parameters import ExpressionParameter
    from ...types import SupportedExpressions




class ENUM_NATIVE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    NATIVE = auto()


class NativeVisitorProtocol(Protocol):

    def visit_expression_node(self, node: NativeExpressionNode) -> SupportedExpressions: ...
    def native(self,  node: NativeExpressionNode) -> SupportedExpressions: ...


class NativeExpressionProtocol(Protocol):

    def native(self,  expr: SupportedExpressions) -> SupportedExpressions: ...


class NativeBuilderProtocol(Protocol):
    """Protocol for native expression builder operations."""

    @staticmethod
    def native(expr: SupportedExpressions) -> "NativeBuilderProtocol":
        """Wrap a native expression."""
        ...
