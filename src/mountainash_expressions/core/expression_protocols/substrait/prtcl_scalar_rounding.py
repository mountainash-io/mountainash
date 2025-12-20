"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, Union, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace


class ScalarRoundingExpressionProtocol(Protocol):
    """Protocol for rounding operations.

    Auto-generated from Substrait rounding extension.
    """

    def ceil(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Rounding to the ceiling of the value `x`.

        Substrait: ceil
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...

    def floor(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Rounding to the floor of the value `x`.

        Substrait: floor
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...

    def round(self, x: SupportedExpressions, /, s: SupportedExpressions, rounding: Any = None) -> SupportedExpressions:
        """Rounding the value `x` to `s` decimal places.

        Substrait: round
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_rounding.yaml
        """
        ...


class ScalarRoundingBuilderProtocol(Protocol):
    """Builder protocol for rounding operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    def ceil(self) -> "BaseNamespace":
        """Round up to the nearest integer.

        Substrait: ceil
        """
        ...

    def floor(self) -> "BaseNamespace":
        """Round down to the nearest integer.

        Substrait: floor
        """
        ...

    def round(
        self,
        decimals: Optional[Union["BaseNamespace", "ExpressionNode", Any, int]] = None,
    ) -> "BaseNamespace":
        """Round to the specified number of decimal places.

        Substrait: round
        """
        ...
