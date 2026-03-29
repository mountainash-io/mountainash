"""If-then (conditional) node for conditional expressions.

Corresponds to Substrait's IfThen message.
"""

from __future__ import annotations
from typing import Any, List, Tuple

from .exn_base import ExpressionNode


class IfThenNode(ExpressionNode):
    """A conditional if-then-else expression.

    Represents a chain of condition-result pairs with a final else clause.
    This is equivalent to SQL's CASE WHEN ... THEN ... ELSE ... END.

    Used for:
    - when().then().otherwise() expressions
    - Ternary logic lowering (t_eq, t_gt, etc. lower to IfThenNode)

    Attributes:
        conditions: List of (condition, result) pairs to evaluate in order.
                   Conditions are evaluated sequentially; first true wins.
        else_clause: The result if no conditions match.

    Examples:
        >>> # Simple: when(x > 0).then(1).otherwise(-1)
        >>> IfThenNode(
        ...     conditions=[(gt_node, LiteralNode(value=1))],
        ...     else_clause=LiteralNode(value=-1)
        ... )
        >>> # Chained: when(x > 10).then("high").when(x > 0).then("low").otherwise("zero")
        >>> IfThenNode(
        ...     conditions=[
        ...         (gt_10_node, LiteralNode(value="high")),
        ...         (gt_0_node, LiteralNode(value="low")),
        ...     ],
        ...     else_clause=LiteralNode(value="zero")
        ... )
    """

    conditions: List[Tuple[ExpressionNode, ExpressionNode]]
    else_clause: ExpressionNode

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_if_then(self)
