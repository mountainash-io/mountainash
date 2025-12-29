"""Mountainash null extension protocol.

Mountainash Extension: Null Handling
URI: file://extensions/functions_null.yaml

Extensions beyond Substrait standard:
- fill_null: Replace NULL values with a specified default value
- null_if: Replace values matching a condition with NULL
"""

from __future__ import annotations

from typing import Union, Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode


class MountainAshNullAPIBuilderProtocol(Protocol):
    """Backend protocol for Mountainash null handling extensions.

    These operations extend Substrait's null handling capabilities with
    additional convenience functions common in DataFrame libraries.
    """

    def fill_null(
        self,
        replacement: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Replace NULL values with the specified replacement value.

        Args:
            input: Expression that may contain NULL values.
            replacement: Value to use in place of NULLs.

        Returns:
            Expression with NULLs replaced by the replacement value.
        """
        ...

    def null_if(
        self,
        value: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Replace values equal to the specified value with NULL.

        This is the inverse of fill_null - useful for cleaning sentinel
        values that represent missing data (e.g., -999, "N/A").

        Args:
            input: Expression to check.
            value: Value that should become NULL.

        Returns:
            Expression with matching values replaced by NULL.
        """
        ...
