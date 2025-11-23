
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any
from typing import Protocol, runtime_checkable
from enum import Enum, auto
from abc import ABC, abstractmethod
from ....types import SupportedExpressions

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS, CONST_EXPRESSION_NATIVE_OPERATORS

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode, NativeBackendExpressionNode
    from ...expression_parameters import ExpressionParameter
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
