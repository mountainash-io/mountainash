"""Narwhals MountainashNameExpressionProtocol implementation.

Implements column naming operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshNameExpressionSystemProtocol


if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class MountainAshNarwhalsNameExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshNameExpressionSystemProtocol):
    """Narwhals implementation of MountainashNameExpressionProtocol."""

    def alias(self, input: NarwhalsExpr, /, name: str) -> NarwhalsExpr:
        """Rename the expression/column.

        Args:
            input: The expression to rename.
            name: The new name.

        Returns:
            The expression with the new name.
        """
        # Extract literal value if needed
        name_val = self._extract_literal_value(name)
        return input.alias(name_val)

    def prefix(self, input: NarwhalsExpr, /, prefix: str) -> NarwhalsExpr:
        """Add a prefix to the column name.

        Args:
            input: The expression.
            prefix: The prefix to add.

        Returns:
            The expression with prefixed name.
        """
        prefix_val = self._extract_literal_value(prefix)
        return input.name.prefix(prefix_val)

    def suffix(self, input: NarwhalsExpr, /, suffix: str) -> NarwhalsExpr:
        """Add a suffix to the column name.

        Args:
            input: The expression.
            suffix: The suffix to add.

        Returns:
            The expression with suffixed name.
        """
        suffix_val = self._extract_literal_value(suffix)
        return input.name.suffix(suffix_val)

    def name_to_upper(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        """Convert column name to uppercase.

        Args:
            input: The expression.

        Returns:
            The expression with uppercase name.
        """
        return input.name.to_uppercase()

    def name_to_lower(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        """Convert column name to lowercase.

        Args:
            input: The expression.

        Returns:
            The expression with lowercase name.
        """
        return input.name.to_lowercase()
