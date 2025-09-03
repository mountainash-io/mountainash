# core/expression_system/parameter.py
from enum import Enum, auto
from typing import Any, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .base import ExpressionSystem
    from ..visitor import ExpressionVisitor

class ParameterType(Enum):
    """Enumeration of parameter types in priority order."""
    EXPRESSION_NODE = auto()      # MountainAsh expression nodes
    NATIVE_EXPRESSION = auto()    # Backend-specific expressions (pl.Expr, nw.Expr)
    COLUMN_REFERENCE = auto()     # String column names
    LITERAL_VALUE = auto()        # Python literals (int, float, bool, None)
    UNKNOWN = auto()              # Cannot determine type

class ExpressionParameter:
    """
    Centralized parameter type detection and conversion.

    This class encapsulates ALL type dispatch logic, providing a clean
    interface for converting various input types to native backend expressions.
    It eliminates scattered type checking throughout the codebase.
    """

    def __init__(
        self,
        value: Any,
        expression_system: 'NativeExpressionSystem',
        visitor: Optional['ExpressionVisitor'] = None
    ):
        """
        Initialize parameter with value and conversion context.

        Args:
            value: The parameter value to be converted
            expression_system: Backend system for native expression creation
            visitor: Optional visitor for recursive MountainAsh node conversion
        """
        self.value = value
        self.expression_system = expression_system
        self.visitor = visitor
        self._type = self._detect_type()

    def _detect_type(self) -> ParameterType:
        """
        Detect parameter type in order of specificity.

        Order matters: check from most specific to least specific.
        """
        # 1. MountainAsh expression nodes (highest priority)
        if self._is_expression_node():
            return ParameterType.EXPRESSION_NODE

        # 2. Native backend expressions
        if self.expression_system.is_native_expression(self.value):
            return ParameterType.NATIVE_EXPRESSION

        # 3. String disambiguation (column vs literal)
        if isinstance(self.value, str):
            if self._looks_like_column_name(self.value):
                return ParameterType.COLUMN_REFERENCE
            else:
                return ParameterType.LITERAL_VALUE

        # 4. Python literals
        if self._is_literal():
            return ParameterType.LITERAL_VALUE

        # 5. Unknown type
        return ParameterType.UNKNOWN

    def _is_expression_node(self) -> bool:
        """Check if value is a MountainAsh expression node."""
        from ...core.logic import ExpressionNode
        return isinstance(self.value, ExpressionNode)

    def _is_literal(self) -> bool:
        """Check if value is a Python literal."""
        return self.value is None or isinstance(self.value, (bool, int, float))

    def _looks_like_column_name(self, s: str) -> bool:
        """
        Heuristic to determine if string is likely a column name.

        Column names typically:
        - Are valid Python identifiers
        - May contain dots for qualified names (table.column)
        - Don't contain spaces or special characters
        """
        # Check for qualified column name (table.column)
        if '.' in s:
            parts = s.split('.')
            return all(part.isidentifier() for part in parts)

        # Simple column name
        return s.isidentifier()

    def to_native_expression(self) -> Any:
        """
        Convert parameter to native backend expression.

        Returns:
            Native expression for the backend

        Raises:
            ValueError: If ExpressionNode conversion requires visitor but none provided
            TypeError: If parameter type cannot be converted
        """
        if self._type == ParameterType.EXPRESSION_NODE:
            if not self.visitor:
                raise ValueError(
                    "Cannot convert ExpressionNode without visitor context. "
                    "Provide visitor when creating ExpressionParameter."
                )
            return self.value.accept(self.visitor)

        elif self._type == ParameterType.NATIVE_EXPRESSION:
            return self.value  # Already in correct format

        elif self._type == ParameterType.COLUMN_REFERENCE:
            return self.expression_system.col(self.value)

        elif self._type == ParameterType.LITERAL_VALUE:
            return self.expression_system.lit(self.value)

        else:
            raise TypeError(
                f"Cannot convert {type(self.value).__name__} to "
                f"{self.expression_system.get_backend_name()} expression. "
                f"Value: {repr(self.value)}"
            )

    @property
    def type_name(self) -> str:
        """Human-readable type name for debugging."""
        return self._type.value

    def __repr__(self) -> str:
        return f"ExpressionParameter(type={self.type_name}, value={repr(self.value)})"
