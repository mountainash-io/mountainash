"""API-builder protocol for Mountainash value operations."""
from __future__ import annotations

from typing import Literal, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshScalarValueAPIBuilderProtocol(Protocol):
    """Fluent API contract for value-domain classification and projection."""

    def value_kind(self) -> BaseExpressionAPI:
        """Return the admitted scalar-domain label for this expression."""
        ...

    def boolean_value(
        self,
        *,
        source: Literal["boolean", "binary_number", "finite_number"] = "boolean",
    ) -> BaseExpressionAPI:
        """Project one selected Boolean-producing domain from this expression."""
        ...

    def text_value(self) -> BaseExpressionAPI:
        """Return text values without stringifying another scalar domain."""
        ...
