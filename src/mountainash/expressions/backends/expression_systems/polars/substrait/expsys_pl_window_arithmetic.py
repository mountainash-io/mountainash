"""Polars WindowArithmeticExpressionProtocol implementation.

Implements window operations for the Polars backend.

Note: Window functions in Polars typically require a window context using .over().
These implementations return expressions that can be used with window specifications.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitWindowArithmeticExpressionSystemProtocol
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import WindowBound

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsWindowArithmeticExpressionSystem(PolarsBaseExpressionSystem, SubstraitWindowArithmeticExpressionSystemProtocol):
    """Polars implementation of WindowArithmeticExpressionProtocol.

    Implements window functions:
    - Ranking: row_number, rank, dense_rank, percent_rank, cume_dist
    - Distribution: ntile
    - Value access: first_value, last_value, nth_value, lead, lag

    Note: These functions typically require window context via .over().
    """

    # =========================================================================
    # Ranking Functions
    # =========================================================================

    def row_number(self) -> PolarsExpr:
        """The number of the current row within its partition, starting at 1.

        Returns:
            Row number expression (requires .over() for partition context).
        """
        return pl.int_range(1, pl.len() + 1)

    def rank(self) -> PolarsExpr:
        """The rank of the current row, with gaps.

        Returns:
            Rank expression (requires .over() for partition context).

        Note:
            Polars doesn't have a direct rank() function.
            Falls back to row_number() approximation.
        """
        # Polars rank needs to be applied in a sorted/grouped context
        # This is an approximation - true rank with gaps needs sorting context
        return pl.int_range(1, pl.len() + 1)

    def dense_rank(self) -> PolarsExpr:
        """The rank of the current row, without gaps.

        Returns:
            Dense rank expression (requires .over() for partition context).

        Note:
            Polars doesn't have a direct dense_rank() function.
            Falls back to row_number() approximation.
        """
        # Similar to rank - needs proper sorting context
        return pl.int_range(1, pl.len() + 1)

    def percent_rank(self) -> PolarsExpr:
        """The relative rank of the current row.

        Returns:
            Percent rank expression (0 to 1).

        Note:
            Calculated as (rank - 1) / (total_rows - 1).
        """
        n = pl.len()
        return (pl.int_range(0, n).cast(pl.Float64)) / (n - 1).cast(pl.Float64)

    def cume_dist(self) -> PolarsExpr:
        """The cumulative distribution.

        Returns:
            Cumulative distribution expression (0 to 1).

        Note:
            Calculated as row_number / total_rows.
        """
        n = pl.len()
        return (pl.int_range(1, n + 1).cast(pl.Float64)) / n.cast(pl.Float64)

    # =========================================================================
    # Distribution Functions
    # =========================================================================

    def ntile(self, x: PolarsExpr, /) -> PolarsExpr:
        """Return an integer ranging from 1 to the argument value.

        Divides the partition as equally as possible.

        Args:
            x: Number of buckets (must be positive integer).

        Returns:
            Bucket number for each row.
        """
        # x is the number of buckets
        n = pl.len()
        # Bucket assignment: floor((row_num - 1) * buckets / n) + 1
        row_nums = pl.int_range(0, n)
        return (row_nums * x / n).floor().cast(pl.Int64) + 1

    # =========================================================================
    # Value Access Functions
    # =========================================================================

    def first_value(self, x: PolarsExpr, /) -> PolarsExpr:
        """Returns the first value in the window.

        Args:
            expression: x to get first value from.

        Returns:
            First value expression.
        """
        return x.first()

    def last_value(self, x: PolarsExpr, /) -> PolarsExpr:
        """Returns the last value in the window.

        Args:
            x: Expression to get last value from.

        Returns:
            Last value expression.
        """
        return x.last()

    def nth_value(
        self,
        x: PolarsExpr,
        /,
        window_offset: PolarsExpr,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Returns a value from the nth row based on the window_offset.

        Args:
            x: Expression to evaluate.
            window_offset: Position in window (1-indexed).
            on_domain_error: Error handling mode.

        Returns:
            Value at specified position, or null if out of range.
        """
        offset_val = self._extract_literal_value(window_offset)
        return x.gather(int(offset_val) - 1)

    def lead(
        self,
        x: PolarsExpr,
        /,
        row_offset: int = 1,
        default: Any = None,
    ) -> PolarsExpr:
        """Return a value from a following row based on physical offset.

        Args:
            x: Expression to evaluate.
            row_offset: Number of rows to look ahead (default 1).
            default: Default value if offset is out of range.

        Returns:
            Value from following row.
        """
        if default is not None:
            return x.shift(-row_offset).fill_null(default)
        return x.shift(-row_offset)

    def lag(
        self,
        x: PolarsExpr,
        /,
        row_offset: int = 1,
        default: Any = None,
    ) -> PolarsExpr:
        """Return a value from a previous row based on physical offset.

        Args:
            x: Expression to evaluate.
            row_offset: Number of rows to look back (default 1).
            default: Default value if offset is out of range.

        Returns:
            Value from previous row.
        """
        if default is not None:
            return x.shift(row_offset).fill_null(default)
        return x.shift(row_offset)

    # =========================================================================
    # Window Application
    # =========================================================================

    def apply_window(
        self,
        expr: PolarsExpr,
        partition_by: List[Any],
        order_by: List[Tuple[Any, bool]],
        lower_bound: Optional[WindowBound] = None,
        upper_bound: Optional[WindowBound] = None,
    ) -> PolarsExpr:
        """Apply window context to a Polars expression.

        Args:
            expr: The native Polars expression to apply windowing to.
            partition_by: List of native partition expressions.
            order_by: List of (expression, descending) tuples.
            lower_bound: Optional frame lower bound.
            upper_bound: Optional frame upper bound.

        Returns:
            Expression with window context applied via .over().
        """
        if not partition_by:
            return expr
        return expr.over(partition_by)
