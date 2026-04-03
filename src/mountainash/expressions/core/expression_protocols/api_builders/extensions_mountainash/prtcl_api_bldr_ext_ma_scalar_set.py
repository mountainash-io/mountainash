"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode



class MountainAshScalarSetAPIBuilderProtocol(Protocol):
    """Builder protocol for set operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def is_in(
        self,
        *values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Check if value is in the given set of values.

        Substrait: index_in (returns bool based on >= 0)
        """
        ...

    def is_not_in(
        self,
        *values: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """Check if value is not in the given set of values.

        Substrait: index_in (returns bool based on < 0)
        """
        ...
