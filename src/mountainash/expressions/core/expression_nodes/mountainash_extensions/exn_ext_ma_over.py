"""Over node -- wraps any expression with window context.

This is the Mountainash extension equivalent of Polars' .over() method.
It takes an arbitrary expression tree and applies a window specification.
"""

from __future__ import annotations

from typing import Any

from ..substrait.exn_base import ExpressionNode
from ..substrait.exn_window_spec import WindowSpec


class OverNode(ExpressionNode):
    """Wraps any expression with window context (Polars .over() pattern).

    Unlike WindowFunctionNode which carries a specific window function key,
    OverNode wraps an arbitrary expression (e.g., col("x").sum()) and adds
    window context via a WindowSpec.

    Attributes:
        expression: The inner expression tree to apply windowing to.
        window_spec: Window specification (partition, order, bounds).
    """

    expression: ExpressionNode
    window_spec: WindowSpec

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_over(self)
