"""Literal node for constant values.

Corresponds to Substrait's Literal message.
"""

from __future__ import annotations
from typing import Any, Optional

from .exn_base import ExpressionNode


class LiteralNode(ExpressionNode):
    """A constant literal value.

    Represents constant values like numbers, strings, booleans, dates, etc.
    Corresponds to Substrait's Literal expression type.

    Attributes:
        value: The literal value (int, float, str, bool, datetime, etc.)
        dtype: Optional type hint for the value (e.g., "i32", "fp64", "string")

    Examples:
        >>> LiteralNode(value=42)
        >>> LiteralNode(value="hello")
        >>> LiteralNode(value=3.14, dtype="fp64")
    """

    value: Any
    dtype: Optional[str] = None

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_literal(self)
