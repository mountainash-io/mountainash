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


class ScalarSetExpressionProtocol(Protocol):
    """Protocol for set operations.

    Auto-generated from Substrait set extension.
    """

    def index_in(self, needle: SupportedExpressions, /, *haystack: SupportedExpressions) -> SupportedExpressions:
        """Return the 0-indexed position of needle in haystack, or -1 if not found.

        Substrait: index_in
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_set.yaml
        """
        ...


class ScalarSetBuilderProtocol(Protocol):
    """Builder protocol for set operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    def is_in(
        self,
        *values: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Check if value is in the given set of values.

        Substrait: index_in (returns bool based on >= 0)
        """
        ...

    def is_not_in(
        self,
        *values: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Check if value is not in the given set of values.

        Substrait: index_in (returns bool based on < 0)
        """
        ...

    def index_in(
        self,
        *values: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Return 0-indexed position in values, or -1 if not found.

        Substrait: index_in
        """
        ...
