"""Ibis WindowArithmeticExpressionProtocol implementation.

Implements window operations for the Ibis backend.

Note: Window functions in Ibis require window context using .over().
These implementations return expressions that can be used with window specifications.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitWindowArithmeticExpressionSystemProtocol
from mountainash.core.constants import WindowBoundType
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import WindowBound

if TYPE_CHECKING:
    from mountainash.core.types import IbisNumericExpr


class SubstraitIbisWindowArithmeticExpressionSystem(IbisBaseExpressionSystem, SubstraitWindowArithmeticExpressionSystemProtocol["IbisNumericExpr"]):
    """Ibis implementation of WindowArithmeticExpressionProtocol.

    Implements window functions:
    - Ranking: row_number, rank, dense_rank, percent_rank, cume_dist
    - Distribution: ntile
    - Value access: first_value, last_value, nth_value, lead, lag

    Note: These functions require window context via .over().
    """

    # =========================================================================
    # Ranking Functions
    # =========================================================================

    def row_number(self, *, order_by_col: IbisNumericExpr | None = None, descending: bool = False) -> IbisNumericExpr:
        """The number of the current row within its partition, starting at 1.

        Args:
            order_by_col: Ignored — Ibis ranking gets ordering from apply_window.
            descending: Ignored — Ibis ranking gets ordering from apply_window.

        Returns:
            Row number expression (requires .over() for partition context).
        """
        return ibis.row_number()

    def rank(self, *, order_by_col: IbisNumericExpr | None = None, descending: bool = False) -> IbisNumericExpr:
        """The rank of the current row, with gaps.

        Args:
            order_by_col: Ignored — Ibis ranking gets ordering from apply_window.
            descending: Ignored — Ibis ranking gets ordering from apply_window.

        Returns:
            Rank expression (requires .over() for partition context).
        """
        return ibis.rank()

    def dense_rank(self, *, order_by_col: IbisNumericExpr | None = None, descending: bool = False) -> IbisNumericExpr:
        """The rank of the current row, without gaps.

        Args:
            order_by_col: Ignored — Ibis ranking gets ordering from apply_window.
            descending: Ignored — Ibis ranking gets ordering from apply_window.

        Returns:
            Dense rank expression (requires .over() for partition context).
        """
        return ibis.dense_rank()

    def percent_rank(self) -> IbisNumericExpr:
        """The relative rank of the current row.

        Returns:
            Percent rank expression (0 to 1).
        """
        return ibis.percent_rank()

    def cume_dist(self) -> IbisNumericExpr:
        """The cumulative distribution.

        Returns:
            Cumulative distribution expression (0 to 1).
        """
        return ibis.cume_dist()

    # =========================================================================
    # Distribution Functions
    # =========================================================================

    def ntile(self, x: IbisNumericExpr, /) -> IbisNumericExpr:
        """Return an integer ranging from 1 to the argument value.

        Divides the partition as equally as possible.

        Args:
            x: Number of buckets (must be positive integer).

        Returns:
            Bucket number for each row.
        """
        return ibis.ntile(x)

    # =========================================================================
    # Value Access Functions
    # =========================================================================

    def first_value(self, x: IbisNumericExpr, /) -> IbisNumericExpr:
        """Returns the first value in the window.

        Args:
            x: Expression to get first value from.

        Returns:
            First value expression.
        """
        return x.first()

    def last_value(self, x: IbisNumericExpr, /) -> IbisNumericExpr:
        """Returns the last value in the window.

        Args:
            x: Expression to get last value from.

        Returns:
            Last value expression.
        """
        return x.last()

    def nth_value(
        self,
        x: IbisNumericExpr,
        /,
        window_offset: IbisNumericExpr,
        on_domain_error: Any = None,
    ) -> IbisNumericExpr:
        """Returns a value from the nth row based on the window_offset.

        Args:
            x: Expression to evaluate.
            window_offset: Position in window (1-indexed).
            on_domain_error: Error handling mode.

        Returns:
            Value at specified position, or null if out of range.
        """
        return x.nth(window_offset - 1)

    def lead(
        self,
        x: IbisNumericExpr,
        /,
        row_offset: int = 1,
        default: Any = None,
    ) -> IbisNumericExpr:
        """Return a value from a following row based on physical offset.

        Args:
            x: Expression to evaluate.
            row_offset: Number of rows to look ahead (default 1).
            default: Default value if offset is out of range.

        Returns:
            Value from following row.
        """
        if default is not None:
            return x.lead(row_offset, default=default)
        return x.lead(row_offset)

    def lag(
        self,
        x: IbisNumericExpr,
        /,
        row_offset: int = 1,
        default: Any = None,
    ) -> IbisNumericExpr:
        """Return a value from a previous row based on physical offset.

        Args:
            x: Expression to evaluate.
            row_offset: Number of rows to look back (default 1).
            default: Default value if offset is out of range.

        Returns:
            Value from previous row.
        """
        if default is not None:
            return x.lag(row_offset, default=default)
        return x.lag(row_offset)

    # =========================================================================
    # Window Application
    # =========================================================================

    def apply_window(
        self,
        expr: IbisNumericExpr,
        partition_by: List[Any],
        order_by: List[Tuple[Any, bool]],
        lower_bound: Optional[WindowBound] = None,
        upper_bound: Optional[WindowBound] = None,
    ) -> IbisNumericExpr:
        """Apply window context to an Ibis expression.

        Args:
            expr: The native Ibis expression to apply windowing to.
            partition_by: List of native partition expressions.
            order_by: List of (expression, descending) tuples.
            lower_bound: Optional frame lower bound.
            upper_bound: Optional frame upper bound.

        Returns:
            Expression with window context applied via .over().
        """
        ibis_order = []
        for col_expr, descending in order_by:
            ibis_order.append(ibis.desc(col_expr) if descending else col_expr)

        window_kwargs: dict[str, Any] = {}
        if partition_by:
            window_kwargs["group_by"] = partition_by
        if ibis_order:
            window_kwargs["order_by"] = ibis_order
        if lower_bound is not None:
            window_kwargs["preceding"] = self._bound_to_ibis(lower_bound)
        if upper_bound is not None:
            window_kwargs["following"] = self._bound_to_ibis(upper_bound)

        window = ibis.window(**window_kwargs)
        return expr.over(window)

    @staticmethod
    def _bound_to_ibis(bound: WindowBound) -> Any:
        """Convert a WindowBound to an Ibis-compatible value.

        Args:
            bound: The window bound to convert.

        Returns:
            Ibis-compatible bound value.
        """
        if bound.bound_type == WindowBoundType.CURRENT_ROW:
            return 0
        elif bound.bound_type in (WindowBoundType.PRECEDING, WindowBoundType.FOLLOWING):
            return bound.offset
        return None  # unbounded
