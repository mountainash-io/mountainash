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

from typing import Protocol

from mountainash.core.types import ExpressionT


class MountainAshNameExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for Mountainash name operations."""

    def alias(
        self,
        input: ExpressionT,
        /,
        name: str,
    ) -> ExpressionT:
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
        input: ExpressionT,
        /,
        prefix: str,
    ) -> ExpressionT:
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
        input: ExpressionT,
        /,
        suffix: str,
    ) -> ExpressionT:
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
        input: ExpressionT,
        /,
    ) -> ExpressionT:
        """Convert column name to uppercase.

        Args:
            input: The expression.

        Returns:
            The expression with uppercase name.
        """
        ...

    def name_to_lower(
        self,
        input: ExpressionT,
        /,
    ) -> ExpressionT:
        """Convert column name to lowercase.

        Args:
            input: The expression.

        Returns:
            The expression with lowercase name.
        """
        ...
