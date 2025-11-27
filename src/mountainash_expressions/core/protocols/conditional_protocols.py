"""Conditional operation protocols.

Defines the three-layer protocol architecture for conditional operations:
- ConditionalVisitorProtocol: Visitor methods for AST traversal
- ConditionalExpressionProtocol: Backend primitive operations
- ConditionalBuilderProtocol: User-facing fluent API
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING, Protocol
from enum import Enum, auto

if TYPE_CHECKING:
    from ...types import SupportedExpressions
    from ..expression_api.base import BaseExpressionAPI


class ENUM_CONDITIONAL_OPERATORS(Enum):
    """
    Enumeration for conditional operators.

    Attributes:
        IF_THEN_ELSE: Conditional if-then-else expression (when/then/otherwise)
    """
    IF_THEN_ELSE = auto()


class ConditionalVisitorProtocol(Protocol):
    """Protocol for conditional expression visitor methods."""

    def if_then_else(
        self,
        node: Any,  # ConditionalExpressionNode
    ) -> SupportedExpressions:
        """Visit an if-then-else conditional node."""
        ...


class ConditionalExpressionProtocol(Protocol):
    """Protocol for backend conditional operations."""

    def if_then_else(
        self,
        condition: SupportedExpressions,
        consequence: SupportedExpressions,
        alternative: SupportedExpressions,
    ) -> SupportedExpressions:
        """Create a conditional if-then-else expression."""
        ...


class ConditionalBuilderProtocol(Protocol):
    """Protocol for conditional builder methods."""

    def when(
        self,
        condition: Any,
    ) -> Any:  # Returns WhenBuilder
        """Start a conditional when-then-otherwise chain."""
        ...
