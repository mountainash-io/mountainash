from __future__ import annotations


from typing import Callable, TYPE_CHECKING, Dict
from enum import Enum


from .expression_visitor import ExpressionVisitor

from ..protocols import ENUM_NATIVE_OPERATORS, NativeVisitorProtocol

from ...types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes import NativeExpressionNode



class NativeExpressionVisitor(ExpressionVisitor,
                            NativeVisitorProtocol,
):

    # ========================================
    # Core Ops
    # ========================================

    @property
    def _native_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_NATIVE_OPERATORS.NATIVE:   self.native,
        }

    # ========================================
    # Core Vistors
    # ========================================

    def visit_expression_node(self, node: NativeExpressionNode) -> SupportedExpressions:
        op_func = self._get_expr_op(self._native_ops, node)
        return op_func(node)


    # ========================================
    # Core Operations
    # ========================================

    def native(self, node: NativeExpressionNode) -> SupportedExpressions:
        """ return a native expression.
            TODO: where do we validate the backend?
        """
        return node.native_expr
