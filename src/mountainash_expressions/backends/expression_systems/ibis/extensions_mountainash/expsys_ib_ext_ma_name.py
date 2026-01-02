"""Ibis MountainashNameExpressionProtocol implementation.

Implements column naming operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshNameExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr



class MountainAshIbisNameExpressionSystem(IbisBaseExpressionSystem, MountainAshNameExpressionSystemProtocol):
    """Ibis implementation of MountainashNameExpressionProtocol."""

    def alias(self, input: IbisExpr, /, name: str) -> IbisExpr:
        """Rename the expression/column.

        Args:
            input: The expression to rename.
            name: The new name.

        Returns:
            The expression with the new name.
        """
        # Extract literal value if needed
        name_val = self._extract_literal_value(name)
        return input.name(name_val)

    def prefix(self, input: IbisExpr, /, prefix: str) -> IbisExpr:
        """Add a prefix to the column name.

        Args:
            input: The expression.
            prefix: The prefix to add.

        Returns:
            The expression with prefixed name.

        Note:
            Ibis doesn't have name.prefix() like Polars.
            We extract the current column name, then rename the expression
            using .name() with the prefixed name.
        """
        prefix_val = self._extract_literal_value(prefix)
        # Get current column name using the helper method
        current_name = self._extract_column_name(input)
        if current_name is not None:
            # Rename the expression with the prefixed name
            return input.name(f"{prefix_val}{current_name}")
        # Fallback for expressions without extractable name
        return input.name(f"{prefix_val}_expr")

    def suffix(self, input: IbisExpr, /, suffix: str) -> IbisExpr:
        """Add a suffix to the column name.

        Args:
            input: The expression.
            suffix: The suffix to add.

        Returns:
            The expression with suffixed name.

        Note:
            Ibis doesn't have name.suffix() like Polars.
            We extract the current column name, then rename the expression
            using .name() with the suffixed name.
        """
        suffix_val = self._extract_literal_value(suffix)
        # Get current column name using the helper method
        current_name = self._extract_column_name(input)
        if current_name is not None:
            # Rename the expression with the suffixed name
            return input.name(f"{current_name}{suffix_val}")
        # Fallback for expressions without extractable name
        return input.name(f"expr_{suffix_val}")

    def name_to_upper(self, input: IbisExpr, /) -> IbisExpr:
        """Convert column name to uppercase.

        Args:
            input: The expression.

        Returns:
            The expression with uppercase name.

        Note:
            Ibis doesn't have name.to_uppercase() like Polars.
            We extract the current column name, then rename the expression
            using .name() with the uppercase name.
        """
        current_name = self._extract_column_name(input)
        if current_name is not None:
            # Rename the expression with uppercase name
            return input.name(current_name.upper())
        return input

    def name_to_lower(self, input: IbisExpr, /) -> IbisExpr:
        """Convert column name to lowercase.

        Args:
            input: The expression.

        Returns:
            The expression with lowercase name.

        Note:
            Ibis doesn't have name.to_lowercase() like Polars.
            We extract the current column name, then rename the expression
            using .name() with the lowercase name.
        """
        current_name = self._extract_column_name(input)
        if current_name is not None:
            # Rename the expression with lowercase name
            return input.name(current_name.lower())
        return input
