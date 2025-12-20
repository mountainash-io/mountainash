"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace


class CastExpressionProtocol(Protocol):
    """Protocol for type casting operations.

    Auto-generated from Substrait cast extension.
    """

    def cast(self, x: SupportedExpressions, /, dtype: Any) -> SupportedExpressions:
        """Cast expression to a target data type.

        Substrait: cast
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/cast.yaml
        """
        ...


class CastBuilderProtocol(Protocol):
    """Builder protocol for type casting operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    def cast(
        self,
        dtype: Union[str, type, Any],
    ) -> "BaseNamespace":
        """Cast to the specified data type.

        Substrait: cast
        """
        ...
