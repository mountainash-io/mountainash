
from typing import Callable, TYPE_CHECKING, Dict, Any, Literal
from abc import ABC, abstractmethod
from enum import Enum
from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS


from ..expression_parameters import ExpressionParameter
from ..expression_system.base import ExpressionSystem
from .expression_visitor import ExpressionVisitor

from ..expression_nodes import SupportedCoreExpressionNodeTypes

from ..protocols import ENUM_CORE_OPERATORS, CoreVisitorProtocol

from ...types import SupportedExpressions


if TYPE_CHECKING:
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
