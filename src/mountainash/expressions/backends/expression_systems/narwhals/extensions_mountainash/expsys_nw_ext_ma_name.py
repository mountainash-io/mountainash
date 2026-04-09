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


class MountainAshNarwhalsNameExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshNameExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of MountainashNameExpressionProtocol."""

    def alias(self, input: NarwhalsExpr, /, name: str) -> NarwhalsExpr:
        """Rename the expression/column.

        Args:
            input: The expression to rename.
            name: The new name.

        Returns:
            The expression with the new name.
        """
        return input.alias(name)

    def prefix(self, input: NarwhalsExpr, /, prefix: str) -> NarwhalsExpr:
        """Add a prefix to the column name.

        Args:
            input: The expression.
            prefix: The prefix to add.

        Returns:
            The expression with prefixed name.
        """
        return input.name.prefix(prefix)

    def suffix(self, input: NarwhalsExpr, /, suffix: str) -> NarwhalsExpr:
        """Add a suffix to the column name.

        Args:
            input: The expression.
            suffix: The suffix to add.

        Returns:
            The expression with suffixed name.
        """
        return input.name.suffix(suffix)

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
