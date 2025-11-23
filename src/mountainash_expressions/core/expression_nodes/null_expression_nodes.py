from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional, final, TYPE_CHECKING, Collection, Literal, Union
from enum import Enum
from typing_extensions import TypeAlias
# from ibis.expr.types import s  # Removed - not used and causes import error

from ...constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES

from .base_expression_node import ExpressionNode

if TYPE_CHECKING:
    from ..expression_visitors import ExpressionVisitor, NullExpressionVisitor
    from ...types import SupportedExpressions



class NullExpressionNode(ExpressionNode):
    """
    Node representing Null operations (SUBTRACT, DIVIDE, etc.).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.ARITHMETIC

    def __init__(self, operator: Enum, left: Any, right: Any):
        self.operator = operator
        self.operand = left
        self.value

    def accept(self, visitor: NullExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: NullExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr



class NullConditionalExpressionNode(ExpressionNode):
    """
    Node representing Null operations (SUBTRACT, DIVIDE, etc.).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.ARITHMETIC

    def __init__(self, operator: Enum, operand: Any, condition: Any):
        self.operator = operator
        self.operand = operand
        self.condition = condition

    def accept(self, visitor: NullExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: NullExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr



class NullConstantExpressionNode(ExpressionNode):
    """
    Node representing arithmetic iterable operations (ADD,  MULTIPLY,).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.NULL_CONSTANT


    def __init__(self, operator: Enum, operand: Any):
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: NullExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: NullExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


class NullLogicalExpressionNode(ExpressionNode):
    """
    Node representing arithmetic iterable operations (ADD,  MULTIPLY,).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.NULL_CONSTANT


    def __init__(self, operator: Enum, operand: Any):
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: NullExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: NullExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr



SupportedNullExpresionNodeTypes: TypeAlias = Union[NullExpressionNode, NullConditionalExpressionNode, NullConstantExpressionNode, NullLogicalExpressionNode]
