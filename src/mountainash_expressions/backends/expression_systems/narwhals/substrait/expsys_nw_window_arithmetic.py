"""Narwhals WindowArithmeticExpressionProtocol implementation.

Implements window operations for the Narwhals backend.

Note: Narwhals has limited window function support.
Many functions are not implemented and will raise NotImplementedError.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitWindowArithmeticExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import NarwhalsExpr


class SubstraitNarwhalsWindowArithmeticExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitWindowArithmeticExpressionSystemProtocol):
    """Narwhals implementation of WindowArithmeticExpressionProtocol.

    Implements window functions:
    - Ranking: row_number, rank, dense_rank, percent_rank, cume_dist
    - Distribution: ntile
    - Value access: first_value, last_value, nth_value, lead, lag

    Note: Narwhals has limited window function support.
    Many functions raise NotImplementedError.
    """

    # =========================================================================
    # Ranking Functions
    # =========================================================================

    def row_number(self) -> NarwhalsExpr:
        """The number of the current row within its partition, starting at 1.

        Raises:
            NotImplementedError: Narwhals doesn't support row_number.
        """
        raise NotImplementedError(
            "row_number() is not supported by the Narwhals backend."
        )

    def rank(self) -> NarwhalsExpr:
        """The rank of the current row, with gaps.

        Raises:
            NotImplementedError: Narwhals doesn't support rank.
        """
        raise NotImplementedError(
            "rank() is not supported by the Narwhals backend."
        )

    def dense_rank(self) -> NarwhalsExpr:
        """The rank of the current row, without gaps.

        Raises:
            NotImplementedError: Narwhals doesn't support dense_rank.
        """
        raise NotImplementedError(
            "dense_rank() is not supported by the Narwhals backend."
        )

    def percent_rank(self) -> NarwhalsExpr:
        """The relative rank of the current row.

        Raises:
            NotImplementedError: Narwhals doesn't support percent_rank.
        """
        raise NotImplementedError(
            "percent_rank() is not supported by the Narwhals backend."
        )

    def cume_dist(self) -> NarwhalsExpr:
        """The cumulative distribution.

        Raises:
            NotImplementedError: Narwhals doesn't support cume_dist.
        """
        raise NotImplementedError(
            "cume_dist() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Distribution Functions
    # =========================================================================

    def ntile(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Return an integer ranging from 1 to the argument value.

        Args:
            x: Number of buckets (must be positive integer).

        Raises:
            NotImplementedError: Narwhals doesn't support ntile.
        """
        raise NotImplementedError(
            "ntile() is not supported by the Narwhals backend."
        )

    # =========================================================================
    # Value Access Functions
    # =========================================================================

    def first_value(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Returns the first value in the window.

        Args:
            x: Expression to get first value from.

        Returns:
            First value expression.
        """
        return x.first()

    def last_value(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Returns the last value in the window.

        Args:
            x: Expression to get last value from.

        Returns:
            Last value expression.
        """
        return x.last()

    def nth_value(
        self,
        x: NarwhalsExpr,
        /,
        window_offset: NarwhalsExpr,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Returns a value from the nth row based on the window_offset.

        Args:
            x: Expression to evaluate.
            window_offset: Position in window (1-indexed).
            on_domain_error: Error handling mode.

        Raises:
            NotImplementedError: Narwhals doesn't support nth_value.
        """
        raise NotImplementedError(
            "nth_value() is not supported by the Narwhals backend."
        )

    def lead(
        self,
        x: NarwhalsExpr,
        /,
        row_offset: int = 1,
        default: Any = None,
    ) -> NarwhalsExpr:
        """Return a value from a following row based on physical offset.

        Args:
            x: Expression to evaluate.
            row_offset: Number of rows to look ahead (default 1).
            default: Default value if offset is out of range.

        Returns:
            Value from following row.
        """
        if default is not None:
            return x.shift(-row_offset).fill_null(nw.lit(default))
        return x.shift(-row_offset)

    def lag(
        self,
        x: NarwhalsExpr,
        /,
        row_offset: int = 1,
        default: Any = None,
    ) -> NarwhalsExpr:
        """Return a value from a previous row based on physical offset.

        Args:
            x: Expression to evaluate.
            row_offset: Number of rows to look back (default 1).
            default: Default value if offset is out of range.

        Returns:
            Value from previous row.
        """
        if default is not None:
            return x.shift(row_offset).fill_null(nw.lit(default))
        return x.shift(row_offset)
