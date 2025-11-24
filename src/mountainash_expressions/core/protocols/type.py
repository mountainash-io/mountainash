
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any, Union
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable
from enum import Enum, auto
from typing_extensions import TypeAlias

from ibis.expr.visualize import get_type


if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode, TypeExpressionNode, SupportedTypeExpressionNodeTypes
    from ..expression_parameters import ExpressionParameter
    from ...types import SupportedExpressions
    from ..expression_builders.base_expression_builder import ExpressionBuilder


class ENUM_TYPE_OPERATORS(Enum):
    """
    Enumeration for expression logical unary operators.
    """
    CAST = auto()

    IS_NUMERIC = auto()
    IS_INT = auto()
    IS_FLOAT = auto()
    IS_STRING = auto()
    IS_BOOL = auto()
    IS_ARRAY = auto()

    GET_TYPE = auto()
    IS_LARGER_TYPE = auto()
    IS_SMALLER_TYPE = auto()
    IS_EQUAL_TYPE = auto()


class TypeVisitorProtocol(Protocol):

    def visit_expression_node(self, node: SupportedTypeExpressionNodeTypes) -> SupportedExpressions: ...
    def cast(self, node: TypeExpressionNode) -> SupportedExpressions: ...

class TypeExpressionProtocol(Protocol):
    def cast(self, operand_expr: SupportedExpressions, type: Any, **kwargs) -> SupportedExpressions: ...

class TypeBuilderProtocol(Protocol):
    def cast(self, type: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
