"""Window arithmetic operations APIBuilder.

Substrait-aligned implementation using WindowFunctionNode.
Provides 11 window function methods that create WindowFunctionNode
instances with window_spec=None (populated later by .over()).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Optional, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import (
    SUBSTRAIT_ARITHMETIC_WINDOW,
    FKEY_MOUNTAINASH_WINDOW,
)
from mountainash.expressions.core.expression_nodes.substrait.exn_scalar_function import ScalarFunctionNode
from mountainash.expressions.core.expression_nodes.substrait.exn_window_function import WindowFunctionNode
from mountainash.expressions.core.expression_nodes.substrait.exn_window_spec import WindowSpec, WindowBound
from mountainash.expressions.core.expression_nodes import LiteralNode, FieldReferenceNode
from mountainash.core.constants import SortField, WindowBoundType

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


_RANK_METHOD_TO_KEY = {
    "average": FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE,
    "min": SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
    "max": FKEY_MOUNTAINASH_WINDOW.RANK_MAX,
    "dense": SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK,
    "ordinal": SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER,
}


class SubstraitWindowArithmeticAPIBuilder(BaseExpressionAPIBuilder):
    """
    Window arithmetic operations APIBuilder (Substrait-aligned).

    Provides window function methods that produce WindowFunctionNode instances.
    The window_spec is left as None until .over() is called on the result.

    Methods:
        rank: Polars-style rank with method parameter
        dense_rank: Alias for rank(method="dense")
        row_number: Alias for rank(method="ordinal")
        percent_rank: Relative rank (0..1)
        cume_dist: Cumulative distribution (0..1)
        ntile: N-tile bucket number
        lead: Value at offset rows after current
        lag: Value at offset rows before current
        first_value: First value in window frame
        last_value: Last value in window frame
        nth_value: Nth value in window frame
    """

    # ========================================
    # Ranking Functions
    # ========================================

    def rank(
        self,
        method: Literal["average", "min", "max", "dense", "ordinal"] = "average",
        *,
        descending: bool = False,
    ) -> BaseExpressionAPI:
        """Rank values within a partition.

        Args:
            method: Ranking method — 'average', 'min' (SQL RANK), 'max',
                    'dense' (SQL DENSE_RANK), 'ordinal' (SQL ROW_NUMBER).
            descending: If True, highest values get rank 1.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        function_key = _RANK_METHOD_TO_KEY[method]

        if isinstance(self._node, FieldReferenceNode):
            col_name = self._node.field
        else:
            raise ValueError(
                "rank() must be called on a column reference, e.g. ma.col('x').rank()"
            )

        node = WindowFunctionNode(
            function_key=function_key,
            arguments=[],
            options={"rank_method": method},
            window_spec=WindowSpec(
                order_by=[SortField(column=col_name, descending=descending)],
            ),
        )
        return self._build(node)

    def dense_rank(self, *, descending: bool = False) -> BaseExpressionAPI:
        """Alias for rank(method="dense").

        Args:
            descending: If True, highest values get rank 1.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        return self.rank(method="dense", descending=descending)

    def row_number(self, *, descending: bool = False) -> BaseExpressionAPI:
        """Alias for rank(method="ordinal").

        Args:
            descending: If True, highest values get rank 1.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        return self.rank(method="ordinal", descending=descending)

    def percent_rank(self) -> BaseExpressionAPI:
        """Relative rank within the partition (0..1).

        Substrait: percent_rank
        No arguments required.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK,
            arguments=[],
        )
        return self._build(node)

    def cume_dist(self) -> BaseExpressionAPI:
        """Cumulative distribution within the partition (0..1).

        Substrait: cume_dist
        No arguments required.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.CUME_DIST,
            arguments=[],
        )
        return self._build(node)

    # ========================================
    # Offset Functions
    # ========================================

    def ntile(self, n: int) -> BaseExpressionAPI:
        """Divide partition into n buckets and return bucket number.

        Substrait: ntile

        Args:
            n: Number of buckets.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.NTILE,
            arguments=[LiteralNode(value=n)],
        )
        return self._build(node)

    def lead(
        self,
        offset: int = 1,
        default: Optional[Union[BaseExpressionAPI, Any]] = None,
    ) -> BaseExpressionAPI:
        """Value at offset rows after current row.

        Substrait: lead

        Args:
            offset: Number of rows ahead (default 1).
            default: Default value if offset is out of bounds.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        arguments: list[Any] = [self._node, LiteralNode(value=offset)]
        if default is not None:
            arguments.append(self._to_substrait_node(default))
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.LEAD,
            arguments=arguments,
        )
        return self._build(node)

    def lag(
        self,
        offset: int = 1,
        default: Optional[Union[BaseExpressionAPI, Any]] = None,
    ) -> BaseExpressionAPI:
        """Value at offset rows before current row.

        Substrait: lag

        Args:
            offset: Number of rows behind (default 1).
            default: Default value if offset is out of bounds.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        arguments: list[Any] = [self._node, LiteralNode(value=offset)]
        if default is not None:
            arguments.append(self._to_substrait_node(default))
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.LAG,
            arguments=arguments,
        )
        return self._build(node)

    # ========================================
    # Value Functions
    # ========================================

    def first_value(self) -> BaseExpressionAPI:
        """First value in the window frame.

        Substrait: first_value

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE,
            arguments=[self._node],
        )
        return self._build(node)

    def last_value(self) -> BaseExpressionAPI:
        """Last value in the window frame.

        Substrait: last_value

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE,
            arguments=[self._node],
        )
        return self._build(node)

    def nth_value(self, n: int) -> BaseExpressionAPI:
        """Nth value in the window frame (1-based)."""
        node = WindowFunctionNode(
            function_key=SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE,
            arguments=[self._node],
            options={"window_offset": n},
        )
        return self._build(node)

    # ========================================
    # Cumulative / Diff Functions
    # ========================================

    def cum_sum(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative sum. Use .over() to partition.

        Args:
            reverse: If True, compute from bottom to top.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        if reverse:
            lower = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
            upper = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
        else:
            lower = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
            upper = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)

        node = WindowFunctionNode(
            function_key=FKEY_MOUNTAINASH_WINDOW.CUM_SUM,
            arguments=[self._node],
            options={"reverse": True} if reverse else {},
            window_spec=WindowSpec(lower_bound=lower, upper_bound=upper),
        )
        return self._build(node)

    def cum_max(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative maximum. Use .over() to partition.

        Args:
            reverse: If True, compute from bottom to top.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        if reverse:
            lower = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
            upper = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
        else:
            lower = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
            upper = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)

        node = WindowFunctionNode(
            function_key=FKEY_MOUNTAINASH_WINDOW.CUM_MAX,
            arguments=[self._node],
            options={"reverse": True} if reverse else {},
            window_spec=WindowSpec(lower_bound=lower, upper_bound=upper),
        )
        return self._build(node)

    def cum_min(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative minimum. Use .over() to partition.

        Args:
            reverse: If True, compute from bottom to top.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        if reverse:
            lower = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
            upper = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
        else:
            lower = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
            upper = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)

        node = WindowFunctionNode(
            function_key=FKEY_MOUNTAINASH_WINDOW.CUM_MIN,
            arguments=[self._node],
            options={"reverse": True} if reverse else {},
            window_spec=WindowSpec(lower_bound=lower, upper_bound=upper),
        )
        return self._build(node)

    def cum_count(self, *, reverse: bool = False) -> BaseExpressionAPI:
        """Cumulative count. Use .over() to partition.

        Args:
            reverse: If True, compute from bottom to top.

        Returns:
            New ExpressionAPI with WindowFunctionNode.
        """
        if reverse:
            lower = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
            upper = WindowBound(bound_type=WindowBoundType.UNBOUNDED_FOLLOWING)
        else:
            lower = WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
            upper = WindowBound(bound_type=WindowBoundType.CURRENT_ROW)

        node = WindowFunctionNode(
            function_key=FKEY_MOUNTAINASH_WINDOW.CUM_COUNT,
            arguments=[self._node],
            options={"reverse": True} if reverse else {},
            window_spec=WindowSpec(lower_bound=lower, upper_bound=upper),
        )
        return self._build(node)

    def diff(self, n: int = 1) -> BaseExpressionAPI:
        """Consecutive difference: value[i] - value[i-n].

        First n elements are null. Works standalone or with .over().

        Args:
            n: Number of slots to shift (default 1).

        Returns:
            New ExpressionAPI with ScalarFunctionNode.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_WINDOW.DIFF,
            arguments=[self._node],
            options={"n": n} if n != 1 else {},
        )
        return self._build(node)
