# core/expression_system/parameter.py
from __future__ import annotations
from enum import Enum, auto
from typing import Any, Optional, TYPE_CHECKING

from ..expression_nodes import ExpressionNode

if TYPE_CHECKING:
    from ..expression_system import ExpressionSystem
    from ..expression_visitors import ExpressionVisitor

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
        expression_system: Optional[ExpressionSystem] = None,
        visitor: Optional[ExpressionVisitor] = None
    ):
        """
        Initialize parameter with value and conversion context.

        Args:
            value: The parameter value to be converted
            expression_system: Optional backend system for native expression creation
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

        # 2. Native backend expressions (only if expression_system available)
        # TODO: Is this needed - can't it be detected by type?
        if self.expression_system and self.expression_system.is_native_expression(self.value):
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
        return isinstance(self.value, ExpressionNode)

    def _is_literal(self) -> bool:
        """Check if value is a Python literal.

        Includes:
        - None
        - bool, int, float
        - datetime, date, time, timedelta
        - list, tuple (for is_in operations)

        Returns:
            bool: True if value is a Python literal, False otherwise.
        """
        from datetime import datetime, date, time, timedelta
        return self.value is None or isinstance(
            self.value,
            (bool, int, float, datetime, date, time, timedelta, list, tuple)
        )

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
            # If visitor provided, use it (for same-type child nodes)
            if self.visitor:
                return self.value.accept(self.visitor)

            # Otherwise, dispatch to appropriate visitor for this node type
            elif self.expression_system:
                from ..expression_visitors import ExpressionVisitorFactory
                from ...constants import CONST_LOGIC_TYPES

                visitor = ExpressionVisitorFactory.get_visitor_for_node(
                    self.value,
                    self.expression_system,
                    CONST_LOGIC_TYPES.BOOLEAN
                )
                return self.value.accept(visitor)

            else:
                raise ValueError(
                    f"ExpressionNode {type(self.value).__name__} requires either visitor or expression_system. "
                    f"Use: ExpressionParameter(value, expression_system=self.backend)"
                )

        elif self._type == ParameterType.NATIVE_EXPRESSION:
            return self.value  # Already in correct format

        elif self._type == ParameterType.COLUMN_REFERENCE:
            return self.expression_system.col(self.value)

        elif self._type == ParameterType.LITERAL_VALUE:
            return self.expression_system.lit(self.value)

        else:
            backend_name = getattr(self.expression_system, 'backend_type', 'unknown')
            if hasattr(backend_name, 'value'):
                backend_name = backend_name.value
            raise TypeError(
                f"Cannot convert {type(self.value).__name__} to "
                f"{backend_name} expression. "
                f"Value: {repr(self.value)}"
            )

    @property
    def type_name(self) -> str:
        """Human-readable type name for debugging."""
        return self._type.value

    def resolve_to_expression_node(self) -> ExpressionNode:
        """
        Resolve parameter to an ExpressionNode.

        This is simpler than to_native_expression - it just checks if the value
        is already an ExpressionNode and returns it as-is. Otherwise, it returns
        the value unchanged (which should be handled by the calling code).

        Returns:
            The value if it's an ExpressionNode, otherwise the value itself

        Note:
            This method is used by visitors to handle parameters that might already
            be expression nodes. For creating new nodes from raw values, the calling
            code should construct the appropriate node type explicitly.
        """
        from ..expression_nodes import ExpressionNode

        if isinstance(self.value, ExpressionNode):
            return self.value
        else:
            # Return the raw value - caller will need to wrap it in appropriate node
            return self.value

    def __repr__(self) -> str:
        return f"ExpressionParameter(type={self.type_name}, value={repr(self.value)})"
