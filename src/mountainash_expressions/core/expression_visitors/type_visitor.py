from __future__ import annotations

from typing import Callable, TYPE_CHECKING, Dict
from enum import Enum

from ..expression_nodes import TypeExpressionNode
from ..expression_parameters import ExpressionParameter
from .expression_visitor import ExpressionVisitor
from ...types import SupportedExpressions
from ..protocols import ENUM_TYPE_OPERATORS, TypeVisitorProtocol

if TYPE_CHECKING:
    from ..expression_nodes import SupportedTypeExpressionNodeTypes


class TypeExpressionVisitor(ExpressionVisitor,
                            TypeVisitorProtocol,
):

    # ========================================
    # Core Ops
    # ========================================

    @property
    def _type_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_TYPE_OPERATORS.CAST:   self.cast,
        }

    # ========================================
    # Core Vistors
    # ========================================

    def visit_expression_node(self, node: SupportedTypeExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._type_ops, node)
        return op_func(node)



    # ========================================
    # Core Operations
    # ========================================

    def cast(self, node: TypeExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()

        return self.backend.cast(operand_expr, node.type)
