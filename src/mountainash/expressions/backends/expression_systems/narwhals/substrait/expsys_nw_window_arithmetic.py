"""Narwhals WindowArithmeticExpressionProtocol implementation.

Implements window operations for the Narwhals backend.

Note: Narwhals has limited window function support.
Many functions are not implemented and will raise NotImplementedError.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitWindowArithmeticExpressionSystemProtocol
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import WindowBound

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsWindowArithmeticExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitWindowArithmeticExpressionSystemProtocol[nw.Expr]):
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

    def row_number(self, *, order_by_col: NarwhalsExpr | None = None, descending: bool = False) -> NarwhalsExpr:
        """The number of the current row within its partition, starting at 1.

        Args:
            order_by_col: Optional ordering column for rank computation.
            descending: Whether to rank in descending order.

        Raises:
            NotImplementedError: When no order_by_col is provided.
        """
        if order_by_col is not None:
            return order_by_col.rank(method="ordinal", descending=descending)
        raise NotImplementedError(
            "row_number() is not supported by the Narwhals backend without order_by."
        )

    def rank(self, *, order_by_col: NarwhalsExpr | None = None, descending: bool = False, rank_method: str = "min", **kwargs: Any) -> NarwhalsExpr:
        """The rank of the current row, with gaps.

        Args:
            order_by_col: Optional ordering column for rank computation.
            descending: Whether to rank in descending order.
            rank_method: Rank method — 'average', 'min', 'max', 'dense', 'ordinal'.

        Raises:
            NotImplementedError: When no order_by_col is provided.
        """
        if order_by_col is not None:
            return order_by_col.rank(method=rank_method, descending=descending)
        raise NotImplementedError(
            "rank() is not supported by the Narwhals backend without order_by."
        )

    def dense_rank(self, *, order_by_col: NarwhalsExpr | None = None, descending: bool = False) -> NarwhalsExpr:
        """The rank of the current row, without gaps.

        Args:
            order_by_col: Optional ordering column for rank computation.
            descending: Whether to rank in descending order.

        Raises:
            NotImplementedError: When no order_by_col is provided.
        """
        if order_by_col is not None:
            return order_by_col.rank(method="dense", descending=descending)
        raise NotImplementedError(
            "dense_rank() is not supported by the Narwhals backend without order_by."
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
        window_offset: Any = 1,
    ) -> NarwhalsExpr:
        """Returns a value from the nth row based on the window_offset.

        Raises:
            NotImplementedError: Narwhals doesn't support nth_value.
        """
        raise NotImplementedError(
            "nth_value() is not supported by the Narwhals backend."
        )

    @staticmethod
    def _coerce_int(value: Any) -> int:
        """Extract plain int from a narwhals literal expression.

        narwhals shift() requires int, but the visitor may pass nw.lit(n).
        """
        if isinstance(value, int):
            return value
        if isinstance(value, nw.Expr) and value._nodes:
            node = value._nodes[0]
            lit_value = getattr(node, "kwargs", {}).get("value")
            if isinstance(lit_value, int):
                return lit_value
        raise TypeError(f"Expected int for row offset, got {type(value).__name__}")

    def lead(
        self,
        x: NarwhalsExpr,
        /,
        row_offset: Any = 1,
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
        n = self._coerce_int(row_offset)
        if default is not None:
            return x.shift(-n).fill_null(nw.lit(default))
        return x.shift(-n)

    def lag(
        self,
        x: NarwhalsExpr,
        /,
        row_offset: Any = 1,
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
        n = self._coerce_int(row_offset)
        if default is not None:
            return x.shift(n).fill_null(nw.lit(default))
        return x.shift(n)

    # =========================================================================
    # Window Application
    # =========================================================================

    @staticmethod
    def _expr_to_col_name(expr: Any) -> str:
        """Extract column name from a narwhals Expr created via nw.col().

        Narwhals .over() accepts strings, not Expr objects. The expression
        visitor produces nw.Expr from FieldReferenceNode — convert back.
        """
        if isinstance(expr, str):
            return expr
        if isinstance(expr, nw.Expr) and expr._nodes:
            node = expr._nodes[0]
            names = getattr(node, "kwargs", {}).get("names")
            if names:
                return names[0]
        raise TypeError(
            f"Cannot extract column name from {type(expr).__name__} for narwhals .over(). "
            f"Narwhals .over() only accepts string column names."
        )

    def apply_window(
        self,
        expr: NarwhalsExpr,
        partition_by: List[Any],
        order_by: List[Tuple[Any, bool]],
        lower_bound: Optional[WindowBound] = None,
        upper_bound: Optional[WindowBound] = None,
    ) -> NarwhalsExpr:
        """Apply window context to a Narwhals expression.

        Narwhals .over() accepts string column names, not Expr objects.
        Partition and order expressions are converted to column name strings.

        Args:
            expr: The native Narwhals expression to apply windowing to.
            partition_by: List of native partition expressions or column names.
            order_by: List of (expression, descending) tuples.
            lower_bound: Optional frame lower bound.
            upper_bound: Optional frame upper bound.

        Returns:
            Expression with window context applied via .over().
        """
        if not partition_by:
            return expr
        str_partition = [self._expr_to_col_name(p) for p in partition_by]
        over_kwargs: dict[str, Any] = {}
        if order_by:
            over_kwargs["order_by"] = [self._expr_to_col_name(col) for col, _ in order_by]
        return expr.over(*str_partition, **over_kwargs)
