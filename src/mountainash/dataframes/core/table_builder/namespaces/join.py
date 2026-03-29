"""
JoinNamespace - DataFrame join operations.

Provides:
    - join(right, on=..., how=...) - General join
    - inner_join(right, on=...) - Inner join
    - left_join(right, on=...) - Left join
    - right_join(right, on=...) - Right join
    - outer_join(right, on=...) - Outer/full join
    - cross_join(right) - Cross/cartesian join
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from ..base import BaseTableBuilder

from ..base import BaseNamespace
from ...protocols import JoinBuilderProtocol


class JoinNamespace(BaseNamespace, JoinBuilderProtocol):
    """
    Namespace for DataFrame join operations.

    All methods return a new TableBuilder instance for chaining.
    """

    def _extract_df(self, other: Union["BaseTableBuilder", Any]) -> Any:
        """Extract DataFrame from TableBuilder or return as-is."""
        # Check if it's a TableBuilder (has both _df and _system)
        # Don't use hasattr(_df) alone as Polars DataFrames have _df internally
        from ..base import BaseTableBuilder

        if isinstance(other, BaseTableBuilder):
            return other._df
        return other

    def join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        how: str = "inner",
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """
        Join with another DataFrame.

        Args:
            right: Right DataFrame or TableBuilder
            on: Column name to join on (if same in both)
            left_on: Column name in left DataFrame
            right_on: Column name in right DataFrame
            how: Join type ('inner', 'left', 'right', 'outer', 'cross')
            suffix: Suffix for duplicate column names

        Returns:
            New TableBuilder with joined data

        Examples:
            # Simple join on same column
            table(left).join(right, on="id")

            # Join on different columns
            table(left).join(right, left_on="user_id", right_on="id")

            # Left join
            table(left).join(right, on="id", how="left")

            # Join with another TableBuilder
            table(left).join(table(right), on="id")
        """
        right_df = self._extract_df(right)
        result = self._system.join(
            self._df,
            right_df,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffix=suffix,
        )
        return self._build(result)

    def inner_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """
        Inner join with another DataFrame.

        Returns only rows that match in both DataFrames.

        Args:
            right: Right DataFrame or TableBuilder
            on: Column name to join on
            left_on: Column name in left DataFrame
            right_on: Column name in right DataFrame
            suffix: Suffix for duplicate columns

        Returns:
            New TableBuilder with inner joined data

        Example:
            table(users).inner_join(orders, on="user_id")
        """
        return self.join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how="inner",
            suffix=suffix,
        )

    def left_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """
        Left join with another DataFrame.

        Returns all rows from left, with matching rows from right.

        Args:
            right: Right DataFrame or TableBuilder
            on: Column name to join on
            left_on: Column name in left DataFrame
            right_on: Column name in right DataFrame
            suffix: Suffix for duplicate columns

        Returns:
            New TableBuilder with left joined data

        Example:
            table(users).left_join(profiles, on="user_id")
        """
        return self.join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how="left",
            suffix=suffix,
        )

    def right_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """
        Right join with another DataFrame.

        Returns all rows from right, with matching rows from left.

        Args:
            right: Right DataFrame or TableBuilder
            on: Column name to join on
            left_on: Column name in left DataFrame
            right_on: Column name in right DataFrame
            suffix: Suffix for duplicate columns

        Returns:
            New TableBuilder with right joined data

        Example:
            table(orders).right_join(users, on="user_id")
        """
        return self.join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how="right",
            suffix=suffix,
        )

    def outer_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """
        Outer (full) join with another DataFrame.

        Returns all rows from both DataFrames.

        Args:
            right: Right DataFrame or TableBuilder
            on: Column name to join on
            left_on: Column name in left DataFrame
            right_on: Column name in right DataFrame
            suffix: Suffix for duplicate columns

        Returns:
            New TableBuilder with outer joined data

        Example:
            table(left).outer_join(right, on="id")
        """
        return self.join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how="outer",
            suffix=suffix,
        )

    def full_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """
        Alias for outer_join.

        Args:
            right: Right DataFrame or TableBuilder
            on: Column name to join on
            left_on: Column name in left DataFrame
            right_on: Column name in right DataFrame
            suffix: Suffix for duplicate columns

        Returns:
            New TableBuilder with full joined data
        """
        return self.outer_join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            suffix=suffix,
        )

    def merge(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        how: str = "inner",
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """
        Alias for join (pandas-style naming).

        Args:
            right: Right DataFrame or TableBuilder
            on: Column name to join on
            left_on: Column name in left DataFrame
            right_on: Column name in right DataFrame
            how: Join type
            suffix: Suffix for duplicate columns

        Returns:
            New TableBuilder with merged data
        """
        return self.join(
            right,
            on=on,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffix=suffix,
        )
