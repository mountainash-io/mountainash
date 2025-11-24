
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any, Iterable, Union
from typing import Protocol, runtime_checkable
from enum import Enum, auto
from ...types import SupportedExpressions
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode
    from ..expression_nodes import NativeExpressionNode

    # from ...expression_parameters import ExpressionParameter
    from ...types import SupportedExpressions
    from ..expression_builders.base_expression_builder import ExpressionBuilder




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


# class NativeBuilderProtocol(Protocol):


    # Native expressions can be parameter to other Nodes
    # def native(self) -> ExpressionBuilder: ...
