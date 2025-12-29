"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING
from mountainash_expressions.types import SupportedExpressions

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode


class SubstraitCastAPIBuilderProtocol(Protocol):
    """Builder protocol for type casting operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def cast(
        self,
        dtype: Union[str, type, Any],
    ) -> BaseExpressionAPI:
        """Cast to the specified data type.

        Substrait: cast
        """
        ...
