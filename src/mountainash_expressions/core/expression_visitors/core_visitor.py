from __future__ import annotations


from typing import Callable, TYPE_CHECKING, Dict
from enum import Enum


from .expression_visitor import ExpressionVisitor

from ..protocols import ENUM_CORE_OPERATORS, CoreVisitorProtocol

from ...types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes import SupportedCoreExpressionNodeTypes
    from ..expression_nodes import (
    ColumnExpressionNode,
    LiteralExpressionNode,
)


class CoreExpressionVisitor(ExpressionVisitor,
                            CoreVisitorProtocol,
):

    # ========================================
    # Core Ops
    # ========================================

    @property
    def _core_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_CORE_OPERATORS.LIT:   self.lit,
            ENUM_CORE_OPERATORS.COL:   self.col,
        }

    # ========================================
    # Core Vistors
    # ========================================

    def visit_expression_node(self, node: SupportedCoreExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._core_ops, node)
        return op_func(node)



    # ========================================
    # Core Operations
    # ========================================

    def lit(self, node: LiteralExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""
        return self.backend.lit(node.value)

    def col(self, node: ColumnExpressionNode) -> SupportedExpressions:
        """Create a column reference expression."""
        return self.backend.col(node.column)
