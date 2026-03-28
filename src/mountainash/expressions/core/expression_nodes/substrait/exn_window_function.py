"""Window function node for Substrait-standard window operations.

Corresponds to Substrait's WindowFunction message. Carries a function key
(rank, row_number, lag, etc.) plus arguments and a window specification.
The window_spec is populated by the .over() API method.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .exn_base import ExpressionNode
from .exn_window_spec import WindowSpec


class WindowFunctionNode(ExpressionNode):
    """A Substrait-standard window function call.

    The function_key identifies which window function (RANK, ROW_NUMBER, LAG, etc.).
    Arguments carry function-specific parameters (e.g., offset for LAG/LEAD).
    The window_spec is None until .over() is called -- compilation will fail without it.

    Attributes:
        function_key: Window function identifier (SUBSTRAIT_ARITHMETIC_WINDOW enum).
        arguments: Function-specific argument nodes (e.g., offset, default value).
        window_spec: Window specification (partition, order, bounds). Set by .over().
        options: Additional function options.
    """

    arguments: List[Any] = []
    window_spec: Optional[WindowSpec] = None
    options: Dict[str, Any] = {}

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_window_function(self)
