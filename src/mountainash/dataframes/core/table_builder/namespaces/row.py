"""
RowNamespace - Row-level operations.

Provides:
    - head(n) - Get first n rows
    - tail(n) - Get last n rows
    - sample(n) - Get random n rows
    - limit(n) - Alias for head
    - take(n) - Alias for head
    - slice(offset, length) - Get slice of rows
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..base import BaseTableBuilder

from ..base import BaseNamespace
from ...protocols import RowBuilderProtocol


class RowNamespace(BaseNamespace, RowBuilderProtocol):
    """
    Namespace for row-level operations.

    All methods return a new TableBuilder instance for chaining.
    """

    def head(self, n: int = 5) -> "BaseTableBuilder":
        """
        Get first n rows.

        Args:
            n: Number of rows (default: 5)

        Returns:
            New TableBuilder with first n rows

        Example:
            table(df).head(10)
        """
        result = self._system.head(self._df, n)
        return self._build(result)

    def tail(self, n: int = 5) -> "BaseTableBuilder":
        """
        Get last n rows.

        Args:
            n: Number of rows (default: 5)

        Returns:
            New TableBuilder with last n rows

        Example:
            table(df).tail(10)
        """
        result = self._system.tail(self._df, n)
        return self._build(result)

    def sample(self, n: int = 5) -> "BaseTableBuilder":
        """
        Get random sample of n rows.

        Args:
            n: Number of rows (default: 5)

        Returns:
            New TableBuilder with random n rows

        Example:
            table(df).sample(100)
        """
        result = self._system.sample(self._df, n)
        return self._build(result)

    def limit(self, n: int) -> "BaseTableBuilder":
        """
        Limit to first n rows.

        Alias for head() (SQL-style naming).

        Args:
            n: Maximum number of rows

        Returns:
            New TableBuilder with at most n rows

        Example:
            table(df).limit(100)
        """
        return self.head(n)

    def take(self, n: int) -> "BaseTableBuilder":
        """
        Take first n rows.

        Alias for head().

        Args:
            n: Number of rows to take

        Returns:
            New TableBuilder with first n rows

        Example:
            table(df).take(50)
        """
        return self.head(n)

    def first(self) -> "BaseTableBuilder":
        """
        Get first row.

        Returns:
            New TableBuilder with first row

        Example:
            table(df).first()
        """
        return self.head(1)

    def last(self) -> "BaseTableBuilder":
        """
        Get last row.

        Returns:
            New TableBuilder with last row

        Example:
            table(df).last()
        """
        return self.tail(1)

    def slice(self, offset: int, length: Optional[int] = None) -> "BaseTableBuilder":
        """
        Get a slice of rows.

        Args:
            offset: Starting row index
            length: Number of rows (None = all remaining)

        Returns:
            New TableBuilder with sliced rows

        Example:
            table(df).slice(10, 20)  # Rows 10-29
        """
        # Use native slicing if available
        df = self._df

        # Different backends handle this differently
        if hasattr(df, "slice"):
            # Polars
            if length is None:
                result = df.slice(offset)
            else:
                result = df.slice(offset, length)
        elif hasattr(df, "iloc"):
            # pandas
            if length is None:
                result = df.iloc[offset:]
            else:
                result = df.iloc[offset : offset + length]
        elif hasattr(df, "limit"):
            # Ibis - use limit with offset
            if length is None:
                total = self._system.get_shape(df)[0]
                length = total - offset
            result = df.limit(length, offset=offset)
        else:
            # Fallback: convert to Polars, slice, convert back

            polars_df = self._system.to_polars(df)
            if length is None:
                sliced = polars_df.slice(offset)
            else:
                sliced = polars_df.slice(offset, length)
            # Try to convert back to original type
            result = sliced

        return self._build(result)

    def skip(self, n: int) -> "BaseTableBuilder":
        """
        Skip first n rows.

        Args:
            n: Number of rows to skip

        Returns:
            New TableBuilder without first n rows

        Example:
            table(df).skip(10)  # All rows except first 10
        """
        return self.slice(n)

    def offset(self, n: int) -> "BaseTableBuilder":
        """
        Alias for skip (SQL-style naming).

        Args:
            n: Number of rows to skip

        Returns:
            New TableBuilder with offset applied

        Example:
            table(df).offset(100).limit(50)
        """
        return self.skip(n)
