from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional, final, TYPE_CHECKING, Collection, Literal, Union
from enum import Enum
from typing_extensions import TypeAlias
# from ibis.expr.types import s  # Removed - not used and causes import error

from ...constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES

from .base_expression_node import ExpressionNode

if TYPE_CHECKING:
    from ..expression_visitors import ExpressionVisitor
    from ..expression_visitors import ArithmeticExpressionVisitor
    from ...types import SupportedExpressions


class BaseArithmeticExpressionNode(ExpressionNode):
    """
    Node representing arithmetic ordered operations (SUBTRACT, DIVIDE, etc.).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.ARITHMETIC

    def __init__(self):
        ...

    def accept(self, visitor: ArithmeticExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: ArithmeticExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


class ArithmeticExpressionNode(ExpressionNode):
    """
    Node representing arithmetic ordered operations (SUBTRACT, DIVIDE, etc.).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    def __init__(self, operator: Enum, left: Any, right: Any):
        self.operator = operator
        self.left = left
        self.right = right


class ArithmeticIterableExpressionNode(ExpressionNode):
    """
    Node representing arithmetic iterable operations (ADD,  MULTIPLY,).

    Arithmetic operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    def __init__(self, operator: Enum, *operands: Any):
        self.operator = operator
        self.operands = operands



SupportedArithmeticExpressionNodeTypes: TypeAlias = Union[ArithmeticExpressionNode, ArithmeticIterableExpressionNode]
