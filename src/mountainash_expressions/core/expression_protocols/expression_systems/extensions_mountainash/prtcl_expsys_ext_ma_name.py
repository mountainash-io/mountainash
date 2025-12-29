"""Mountainash name extension protocol.

Mountainash Extension: Name
URI: file://extensions/functions_name.yaml

Extensions beyond Substrait standard:
- alias: Rename a column
- prefix: Add prefix to column name
- suffix: Add suffix to column name
- name_to_upper: Convert column name to uppercase
- name_to_lower: Convert column name to lowercase
"""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ....types import SupportedExpressions


class MountainAshNameExpressionSystemProtocol(Protocol):
    """Backend protocol for Mountainash name operations."""

    def alias(
        self,
        input: "SupportedExpressions",
        /,
        name: str,
    ) -> "SupportedExpressions":
        """Rename the expression/column.

        Args:
            input: The expression to rename.
            name: The new name.

        Returns:
            The expression with the new name.
        """
        ...

    def prefix(
        self,
        input: "SupportedExpressions",
        /,
        prefix: str,
    ) -> "SupportedExpressions":
        """Add a prefix to the column name.

        Args:
            input: The expression.
            prefix: The prefix to add.

        Returns:
            The expression with prefixed name.
        """
        ...

    def suffix(
        self,
        input: "SupportedExpressions",
        /,
        suffix: str,
    ) -> "SupportedExpressions":
        """Add a suffix to the column name.

        Args:
            input: The expression.
            suffix: The suffix to add.

        Returns:
            The expression with suffixed name.
        """
        ...

    def name_to_upper(
        self,
        input: "SupportedExpressions",
        /,
    ) -> "SupportedExpressions":
        """Convert column name to uppercase.

        Args:
            input: The expression.

        Returns:
            The expression with uppercase name.
        """
        ...

    def name_to_lower(
        self,
        input: "SupportedExpressions",
        /,
    ) -> "SupportedExpressions":
        """Convert column name to lowercase.

        Args:
            input: The expression.

        Returns:
            The expression with lowercase name.
        """
        ...
