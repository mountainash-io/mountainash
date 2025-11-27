from __future__ import annotations


from typing import Callable, TYPE_CHECKING, Dict
from enum import Enum


from ..expression_parameters import ExpressionParameter
from .expression_visitor import ExpressionVisitor


from ..protocols import ENUM_NAME_OPERATORS, NameVisitorProtocol

from ...types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes import (
        NameAliasExpressionNode,
        NamePrefixExpressionNode,
        NameSuffixExpressionNode,
        NameExpressionNode,
        SupportedNameExpressionNodeTypes

)


class NameExpressionVisitor(ExpressionVisitor,
                            NameVisitorProtocol
):

    # ========================================
    # Core Ops
    # ========================================

    @property
    def _name_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_NAME_OPERATORS.ALIAS:   self.alias,
            ENUM_NAME_OPERATORS.NAME_PREFIX:  self.prefix,
            ENUM_NAME_OPERATORS.NAME_SUFFIX:  self.suffix,
            ENUM_NAME_OPERATORS.NAME_TO_UPPER: self.to_upper,
            ENUM_NAME_OPERATORS.NAME_TO_LOWER: self.to_lower,
        }

    # ========================================
    # Core Vistors
    # ========================================

    def visit_expression_node(self, node: SupportedNameExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._name_ops, node)
        return op_func(node)



    # ========================================
    # Core Operations
    # ========================================

    def alias(self, node: NameAliasExpressionNode) -> SupportedExpressions:

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.alias(operand_expr, node.alias)

    def prefix(self, node: NamePrefixExpressionNode) -> SupportedExpressions:

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.prefix(operand_expr, node.prefix)

    def suffix(self, node: NameSuffixExpressionNode) -> SupportedExpressions:

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.suffix(operand_expr, node.suffix)

    def to_upper(self, node: NameExpressionNode) -> SupportedExpressions:

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.to_upper(operand_expr)

    def to_lower(self, node: NameExpressionNode) -> SupportedExpressions:

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.to_lower(operand_expr)
