"""Ibis WindowArithmeticExpressionProtocol implementation.

Implements window operations for the Ibis backend.

Note: Window functions in Ibis require window context using .over().
These implementations return expressions that can be used with window specifications.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitWindowArithmeticExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import IbisExpr


class SubstraitIbisWindowArithmeticExpressionSystem(IbisBaseExpressionSystem, SubstraitWindowArithmeticExpressionSystemProtocol):
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

    def row_number(self) -> IbisExpr:
        """The number of the current row within its partition, starting at 1.

        Returns:
            Row number expression (requires .over() for partition context).
        """
        return ibis.row_number()

    def rank(self) -> IbisExpr:
        """The rank of the current row, with gaps.

        Returns:
            Rank expression (requires .over() for partition context).
        """
        return ibis.rank()

    def dense_rank(self) -> IbisExpr:
        """The rank of the current row, without gaps.

        Returns:
            Dense rank expression (requires .over() for partition context).
        """
        return ibis.dense_rank()

    def percent_rank(self) -> IbisExpr:
        """The relative rank of the current row.

        Returns:
            Percent rank expression (0 to 1).
        """
        return ibis.percent_rank()

    def cume_dist(self) -> IbisExpr:
        """The cumulative distribution.

        Returns:
            Cumulative distribution expression (0 to 1).
        """
        return ibis.cume_dist()

    # =========================================================================
    # Distribution Functions
    # =========================================================================

    def ntile(self, x: IbisExpr, /) -> IbisExpr:
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

    def first_value(self, x: IbisExpr, /) -> IbisExpr:
        """Returns the first value in the window.

        Args:
            x: Expression to get first value from.

        Returns:
            First value expression.
        """
        return x.first()

    def last_value(self, x: IbisExpr, /) -> IbisExpr:
        """Returns the last value in the window.

        Args:
            x: Expression to get last value from.

        Returns:
            Last value expression.
        """
        return x.last()

    def nth_value(
        self,
        x: IbisExpr,
        /,
        window_offset: IbisExpr,
        on_domain_error: Any = None,
    ) -> IbisExpr:
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
        x: IbisExpr,
        /,
        row_offset: int = 1,
        default: Any = None,
    ) -> IbisExpr:
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
        x: IbisExpr,
        /,
        row_offset: int = 1,
        default: Any = None,
    ) -> IbisExpr:
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
