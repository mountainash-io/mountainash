from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Dict
from enum import Enum

# from pandas.core.arrays.datetimelike import isin


from .expression_visitor import ExpressionVisitor
from ..expression_parameters import ExpressionParameter
from functools import reduce
from ...types import SupportedExpressions


from ..expression_nodes import IterableExpressionNode

from ..protocols import IterableVisitorProtocol, ENUM_ITERABLE_OPERATORS

if TYPE_CHECKING:
    from ..expression_nodes import SupportedIterableExpressionNodeTypes



class IterableExpressionVisitor(ExpressionVisitor,
                              IterableVisitorProtocol):

    # ===============
    # Operations Maps
    # ===============

    @property
    def _iterable_ops(self) -> Dict[Enum, Callable]:

        return {
            ENUM_ITERABLE_OPERATORS.COALESCE:        self.coalesce,
            ENUM_ITERABLE_OPERATORS.GREATEST:        self.greatest,
            ENUM_ITERABLE_OPERATORS.LEAST:           self.least,
        }


    # ===============
    # Expression Visitor Methods
    # ===============



    # ===============
    # Logical Expressions
    def visit_expression_node(self, node: SupportedIterableExpressionNodeTypes) -> SupportedExpressions:

        op_func = self._get_expr_op(self._iterable_ops, node)
        return op_func(node)

    # Horizontal Iterable Operations
    # ===============

    def coalesce(self, node: IterableExpressionNode) -> SupportedExpressions:

        if not isinstance(node, IterableExpressionNode):
            raise TypeError(f"Expected IterableIterableExpressionNode, got {type(node)}")

        expr_list = [ ExpressionParameter(operand, expression_system=self.backend).to_native_expression() for operand in node.operands ]

        return reduce(lambda x, y: self.backend.coalesce(x, y), expr_list)

    def greatest(self, node: IterableExpressionNode) -> SupportedExpressions:
        # Process all operands
        expr_list = [ ExpressionParameter(operand, expression_system=self.backend).to_native_expression() for operand in node.operands ]

        return reduce(lambda x, y: self.backend.greatest(x, y), expr_list)

    def least(self, node: IterableExpressionNode) -> SupportedExpressions:

        # Process all operands
        expr_list = [ ExpressionParameter(operand, expression_system=self.backend).to_native_expression() for operand in node.operands ]

        return reduce(lambda x, y: self.backend.least(x, y), expr_list)
