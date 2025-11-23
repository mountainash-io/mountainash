from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional, final, TYPE_CHECKING, Collection, Literal, Union
from enum import Enum
from typing_extensions import TypeAlias
# from ibis.expr.types import s  # Removed - not used and causes import error

from ...constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES

from .base_expression_node import ExpressionNode

if TYPE_CHECKING:
    from ..expression_visitors.expression_visitor import ExpressionVisitor
    from ..expression_visitors import CoreExpressionVisitor
    from ..protocols import ENUM_CORE_OPERATORS
    from ...types import SupportedExpressions



class NativeBackendExpressionNode(ExpressionNode):

    # @property
    # @final
    # def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
    #     return CONST_EXPRESSION_NODE_TYPES.NATIVE

    def __init__(self, operator: Enum, native_expr: Any):
        self.operator = operator
        self.native_expr = native_expr


class ColumnExpressionNode(ExpressionNode):

    # @property
    # @final
    # def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
    #     return CONST_EXPRESSION_NODE_TYPES.COLUMN

    def __init__(self, operator: ENUM_CORE_OPERATORS, column: str):
        self.operator = operator
        self.column = column


    def accept(self, visitor: CoreExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: CoreExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


class LiteralExpressionNode(ExpressionNode):
    """
    Literal value expression node.

    Represents a constant literal value (string, number, boolean, etc.).
    """

    # @property
    # @final
    # def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
    #     return CONST_EXPRESSION_NODE_TYPES.LITERAL

    # @property
    # def logic_type(self) -> CONST_LOGIC_TYPES:
    #     """Literals work with any logic system."""
    #     return CONST_LOGIC_TYPES.BOOLEAN

    def __init__(self, operator: ENUM_CORE_OPERATORS, value: Any):
        self.operator = operator
        self.value = value

    def accept(self, visitor: CoreExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: CoreExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


SupportedCoreExpressionNodeTypes: TypeAlias = Union[NativeBackendExpressionNode, ColumnExpressionNode, LiteralExpressionNode]
