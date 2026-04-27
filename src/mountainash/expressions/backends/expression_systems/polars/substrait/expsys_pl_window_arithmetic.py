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


class SubstraitPolarsWindowArithmeticExpressionSystem(PolarsBaseExpressionSystem, SubstraitWindowArithmeticExpressionSystemProtocol[pl.Expr]):
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

    def row_number(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
        """The number of the current row within its partition, starting at 1.

        Args:
            order_by_col: Optional ordering column for rank computation.
            descending: Whether to rank in descending order.

        Returns:
            Row number expression (requires .over() for partition context).
        """
        if order_by_col is not None:
            return order_by_col.rank(method="ordinal", descending=descending)
        return pl.int_range(1, pl.len() + 1)

    def rank(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
        """The rank of the current row, with gaps.

        Args:
            order_by_col: Optional ordering column for rank computation.
            descending: Whether to rank in descending order.

        Returns:
            Rank expression (requires .over() for partition context).
        """
        if order_by_col is not None:
            return order_by_col.rank(method="min", descending=descending)
        return pl.int_range(1, pl.len() + 1)

    def dense_rank(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
        """The rank of the current row, without gaps.

        Args:
            order_by_col: Optional ordering column for rank computation.
            descending: Whether to rank in descending order.

        Returns:
            Dense rank expression (requires .over() for partition context).
        """
        if order_by_col is not None:
            return order_by_col.rank(method="dense", descending=descending)
        return pl.int_range(1, pl.len() + 1)

    def percent_rank(self, *, order_by_col: PolarsExpr | None = None, descending: bool = False) -> PolarsExpr:
        """The relative rank of the current row.

        Args:
            order_by_col: Optional ordering column for rank computation.
            descending: Whether to rank in descending order.

        Returns:
            Percent rank expression (0 to 1).
        """
        if order_by_col is not None:
            r = order_by_col.rank(method="min", descending=descending)
            n = pl.len()
            return (r.cast(pl.Float64) - 1) / (n - 1).cast(pl.Float64)
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
        window_offset: Any = 1,
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
        return x.gather(window_offset - 1)

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
        if not partition_by and not order_by:
            return expr
        over_kwargs: dict[str, Any] = {}
        if order_by:
            order_cols = [col for col, _ in order_by]
            desc_flags = [desc for _, desc in order_by]
            over_kwargs["order_by"] = order_cols if len(order_cols) > 1 else order_cols[0]
            # Polars .over() accepts descending as a single bool
            if any(desc_flags):
                over_kwargs["descending"] = True
        if partition_by:
            return expr.over(*partition_by, **over_kwargs)
        return expr.over(**over_kwargs)
