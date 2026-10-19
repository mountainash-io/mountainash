"""Scalar function node for function calls.

Corresponds to Substrait's ScalarFunction message.
"""

from __future__ import annotations
import dataclasses
from collections.abc import Mapping
from typing import Any, Dict, List
from pydantic import Field, SerializationInfo, SerializerFunctionWrapHandler, field_serializer

from .exn_base import ExpressionNode
from ...expression_system.function_keys.enums import (
    MOUNTAINASH_TERNARY_NON_TERMINAL,
    MOUNTAINASH_TERNARY_ALL,
)



class _ImmutableDiagnosticContext(dict[str, str]):
    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("diagnostic_context is immutable")

    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = _immutable
    __ior__ = _immutable


def _json_option_value(value: Any) -> Any:
    """Plain JSON shape for owned declaration values (mapping proxies, frozen dataclasses)."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _json_option_value(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {key: _json_option_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_option_value(item) for item in value]
    return value



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
        >>> from mountainash.expressions.core.expression_system.function_keys.enums import (
        ...     FKEY_SUBSTRAIT_SCALAR_COMPARISON, FKEY_SUBSTRAIT_SCALAR_STRING
        ... )
        >>> ScalarFunctionNode(function=FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL, arguments=[left, right])
        >>> ScalarFunctionNode(function=FKEY_SUBSTRAIT_SCALAR_STRING.UPPER, arguments=[col])
    """

    # # Function identifier - Enum preferred, str for backward compatibility
    # function_key: Enum
    # substrait_name: str
    arguments: List[ExpressionNode]
    options: Dict[str, Any] = {}
    diagnostic_context: Dict[str, str] = Field(default_factory=dict)


    def model_post_init(self, __context: Any) -> None:
        object.__setattr__(
            self,
            "diagnostic_context",
            _ImmutableDiagnosticContext(self.diagnostic_context),
        )

    @field_serializer("options", mode="wrap")
    def _serialize_options(
        self, value: Dict[str, Any], handler: SerializerFunctionWrapHandler, info: SerializationInfo,
    ) -> Any:
        return handler(_json_option_value(value) if info.mode_is_json() else value)


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
