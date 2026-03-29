"""
Horizontal operations protocols.

Horizontal operations work row-wise across multiple columns:
- coalesce: first non-null value
- greatest: maximum value across columns
- least: minimum value across columns
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union
from typing import Protocol
from enum import Enum, auto
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode, HorizontalExpressionNode, SupportedHorizontalExpressionNodeTypes
    from ...types import SupportedExpressions
    from ..namespaces import BaseNamespace

    validHorizontalExpressionNodes: TypeAlias = HorizontalExpressionNode


class ENUM_HORIZONTAL_OPERATORS(Enum):
    """
    Enumeration for horizontal operators.

    Horizontal operations work across multiple columns for each row.
    """
    COALESCE = auto()
    GREATEST = auto()
    LEAST = auto()


class HorizontalVisitorProtocol(Protocol):
    """Protocol for horizontal operation visitors."""

    def visit_expression_node(self, node: SupportedHorizontalExpressionNodeTypes) -> SupportedExpressions: ...

    def coalesce(self, node: HorizontalExpressionNode) -> SupportedExpressions: ...
    def greatest(self, node: HorizontalExpressionNode) -> SupportedExpressions: ...
    def least(self,    node: HorizontalExpressionNode) -> SupportedExpressions: ...


class HorizontalExpressionProtocol(Protocol):
    """Protocol for backend horizontal operations."""

    def coalesce(self, *operands: SupportedExpressions) -> SupportedExpressions: ...
    def greatest(self, *operands: SupportedExpressions) -> SupportedExpressions: ...
    def least(self,    *operands: SupportedExpressions) -> SupportedExpressions: ...


class HorizontalBuilderProtocol(Protocol):
    """Protocol for horizontal operation builders."""

    def coalesce(self, *other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def greatest(self, *other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
    def least(self,    *other: Union[BaseNamespace, ExpressionNode, Any]) -> BaseNamespace: ...
