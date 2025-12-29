"""Scalar function node for function calls.

Corresponds to Substrait's ScalarFunction message.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Union

from .exn_base import ExpressionNode
from ..expression_system.function_keys.enums import (
    MOUNTAINASH_TERNARY_NON_TERMINAL,
    MOUNTAINASH_TERNARY_ALL,
)


class ScalarFunctionNode(ExpressionNode):
    """A scalar function call.

    Represents a function applied to zero or more arguments.
    This is the universal node type for most operations - comparisons,
    arithmetic, string functions, etc. all become ScalarFunctionNode.

    The function identifier should be an Enum from the function_keys.enums module
    for type safety and IDE autocomplete.

    The function maps to the FunctionRegistry to determine:
    - The Substrait URI and function name for serialization
    - The backend method name for compilation

    Attributes:
        function: Function identifier (Enum from function_keys.enums)
        arguments: List of argument nodes
        options: Function-specific options (e.g., precision for is_close)

    Examples:
        >>> from mountainash_expressions.core.expression_system.function_keys.enums import (
        ...     KEY_SCALAR_COMPARISON, KEY_SCALAR_STRING
        ... )
        >>> ScalarFunctionNode(function=KEY_SCALAR_COMPARISON.EQUAL, arguments=[left, right])
        >>> ScalarFunctionNode(function=KEY_SCALAR_STRING.UPPER, arguments=[col])
    """

    # # Function identifier - Enum preferred, str for backward compatibility
    # function_key: Enum
    # substrait_name: str
    arguments: List[ExpressionNode]
    options: Dict[str, Any] = {}

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_scalar_function(self)

    @property
    def is_ternary_non_terminal(self) -> bool:
        """Return True if this node produces ternary values (-1/0/1).

        Non-terminal ternary functions need booleanization before use in filters.
        This property enables automatic coercion in namespace operations.
        """
        return self.function_key in MOUNTAINASH_TERNARY_NON_TERMINAL

    @property
    def is_ternary(self) -> bool:
        """Return True if this is any ternary operation (terminal or non-terminal)."""
        return self.function_key in MOUNTAINASH_TERNARY_ALL
