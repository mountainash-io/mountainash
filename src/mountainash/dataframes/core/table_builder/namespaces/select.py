"""
SelectNamespace - Column selection and manipulation operations.

Provides:
    - select(*columns) - Select columns
    - drop(*columns) - Drop columns
    - rename(mapping) - Rename columns
    - reorder(*columns) - Reorder columns
    - with_columns(**exprs) - Add/modify columns
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from ..base import BaseTableBuilder

from ..base import BaseNamespace
from ...protocols import SelectBuilderProtocol


class SelectNamespace(BaseNamespace, SelectBuilderProtocol):
    """
    Namespace for column selection and manipulation operations.

    All methods return a new TableBuilder instance for chaining.
    """

    def select(self, *columns: str) -> "BaseTableBuilder":
        """
        Select columns from DataFrame.

        Args:
            *columns: Column names to select

        Returns:
            New TableBuilder with selected columns

        Example:
            table(df).select("id", "name", "value")
        """
        col_list = list(columns)
        result = self._system.select(self._df, col_list)
        return self._build(result)

    def drop(self, *columns: str) -> "BaseTableBuilder":
        """
        Drop columns from DataFrame.

        Args:
            *columns: Column names to drop

        Returns:
            New TableBuilder without dropped columns

        Example:
            table(df).drop("temp_col", "debug_col")
        """
        col_list = list(columns)
        result = self._system.drop(self._df, col_list)
        return self._build(result)

    def rename(self, mapping: Dict[str, str]) -> "BaseTableBuilder":
        """
        Rename columns in DataFrame.

        Args:
            mapping: Dict mapping old names to new names

        Returns:
            New TableBuilder with renamed columns

        Example:
            table(df).rename({"old_name": "new_name"})
        """
        result = self._system.rename(self._df, mapping)
        return self._build(result)

    def reorder(self, *columns: str) -> "BaseTableBuilder":
        """
        Reorder columns in DataFrame.

        Args:
            *columns: Column names in desired order

        Returns:
            New TableBuilder with reordered columns

        Example:
            table(df).reorder("id", "name", "value", "created_at")
        """
        col_list = list(columns)
        result = self._system.reorder(self._df, col_list)
        return self._build(result)

    def alias(self, column: str, new_name: str) -> "BaseTableBuilder":
        """
        Alias (rename) a single column.

        Convenience method for renaming one column.

        Args:
            column: Current column name
            new_name: New column name

        Returns:
            New TableBuilder with renamed column

        Example:
            table(df).alias("value", "amount")
        """
        return self.rename({column: new_name})

    def keep(self, *columns: str) -> "BaseTableBuilder":
        """
        Alias for select - keep only specified columns.

        Args:
            *columns: Column names to keep

        Returns:
            New TableBuilder with only specified columns

        Example:
            table(df).keep("id", "name")
        """
        return self.select(*columns)

    def exclude(self, *columns: str) -> "BaseTableBuilder":
        """
        Alias for drop - exclude specified columns.

        Args:
            *columns: Column names to exclude

        Returns:
            New TableBuilder without specified columns

        Example:
            table(df).exclude("internal_id", "debug_flag")
        """
        return self.drop(*columns)
