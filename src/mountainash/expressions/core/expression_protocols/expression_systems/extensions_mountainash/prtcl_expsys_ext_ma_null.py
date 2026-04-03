"""Mountainash null extension protocol.

Mountainash Extension: Null Handling
URI: file://extensions/functions_null.yaml

Extensions beyond Substrait standard:
- fill_null: Replace NULL values with a specified default value
- null_if: Replace values matching a condition with NULL
- fill_nan: Replace NaN values with a specified value
"""

from __future__ import annotations

from typing import Any, Protocol

from mountainash.core.types import ExpressionT


class MountainAshNullExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for Mountainash null handling extensions.

    These operations extend Substrait's null handling capabilities with
    additional convenience functions common in DataFrame libraries.
    """

    def fill_null(
        self,
        input: ExpressionT,
        replacement: Any,
        /,
    ) -> ExpressionT:
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
        input: ExpressionT,
        condition: Any,
        /,
    ) -> ExpressionT:
        """Replace values matching a condition with NULL.

        Args:
            input: Expression to conditionally nullify.
            condition: Value that, when matched, produces NULL.

        Returns:
            Expression with matching values replaced by NULL.
        """
        ...

    def fill_nan(
        self,
        input: ExpressionT,
        replacement: Any,
        /,
    ) -> ExpressionT:
        """Replace NaN values with the specified replacement value."""
        ...

