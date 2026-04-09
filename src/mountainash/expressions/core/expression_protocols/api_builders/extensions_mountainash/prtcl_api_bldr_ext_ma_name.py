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

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshNameAPIBuilderProtocol(Protocol):
    """Backend protocol for Mountainash name operations."""

    def alias(
        self,
        name: str,
    ) -> BaseExpressionAPI:
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
        prefix: str,
    ) -> BaseExpressionAPI:
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
        suffix: str,
    ) -> BaseExpressionAPI:
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
    ) -> BaseExpressionAPI:
        """Convert column name to uppercase.

        Args:
            input: The expression.

        Returns:
            The expression with uppercase name.
        """
        ...

    def name_to_lower(
        self,
    ) -> BaseExpressionAPI:
        """Convert column name to lowercase.

        Args:
            input: The expression.

        Returns:
            The expression with lowercase name.
        """
        ...

    # Polars-compatible aliases
    def to_lowercase(self, /) -> BaseExpressionAPI:
        """Alias for name_to_lower() — Polars compatibility."""
        ...

    def to_uppercase(self, /) -> BaseExpressionAPI:
        """Alias for name_to_upper() — Polars compatibility."""
        ...
