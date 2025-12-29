"""Mountainash null extension protocol.

Mountainash Extension: Null Handling
URI: file://extensions/functions_null.yaml

Extensions beyond Substrait standard:
- fill_null: Replace NULL values with a specified default value
- null_if: Replace values matching a condition with NULL
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions


class MountainAshNullExpressionSystemProtocol(Protocol):
    """Backend protocol for Mountainash null handling extensions.

    These operations extend Substrait's null handling capabilities with
    additional convenience functions common in DataFrame libraries.
    """

    def fill_null(
        self,
        input: "SupportedExpressions",
        replacement: "SupportedExpressions",
        /,
    ) -> "SupportedExpressions":
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
        input: "SupportedExpressions",
        value: "SupportedExpressions",
        /,
    ) -> "SupportedExpressions":
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
