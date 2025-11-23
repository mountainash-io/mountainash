from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List, Callable, Optional, final, TYPE_CHECKING, Collection, Literal
from enum import Enum
# from ibis.expr.types import s  # Removed - not used and causes import error

from ...constants import CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES

from ..base_expression_node import ExpressionNode

if TYPE_CHECKING:
    from ..expression_visitors.expression_visitor import ExpressionVisitor
    from ..expression_visitors import StringExpressionVisitor
    from ...types import SupportedExpressions


    StringExpressionNode,
    StringIterableExpressionNode,
    StringLogicalExpressionNode,
    PatternExpressionNode,
    PatternLogicalExpressionNode


class BaseStringExpressionNode(ExpressionNode):
    """
    Node representing string operations (UPPER, LOWER, TRIM, SUBSTRING, etc.).

    String operations return string values (or integers for LENGTH) and are universal
    across all logic systems.

    Supports both:
    - Unary operations: UPPER, LOWER, TRIM, LENGTH (just operand)
    - Operations with arguments: SUBSTRING(start, end), REPLACE(old, new), CONCAT(*args)
    """

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.STRING


    def accept(self, visitor: StringExpressionVisitor) -> Any:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: StringExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


class StringExpressionNode(BaseStringExpressionNode):

    def __init__(self, operator: str, operand: Any, *args, **kwargs):
        self.operator = operator
        self.operand = operand
        self.substring = substring
        self.prefix = prefix
        self.suffix = suffix
        self.old = old
        self.new = new
        self.start = start
        self.length = length


class StringSuffixExpressionNode(BaseStringExpressionNode):

    def __init__(self, operator: str, operand: Any, suffix: Any):
        self.operator = operator
        self.operand = operand
        self.suffix = suffix


class StringPrefixExpressionNode(BaseStringExpressionNode):

    def __init__(self, operator: str, operand: Any, prefix: Any):
        self.operator = operator
        self.operand = operand
        self.prefix = prefix


class StringLengthExpressionNode(BaseStringExpressionNode):

    def __init__(self, operator: str, operand: Any, start: Any, length:Any):
        self.operator = operator
        self.operand = operand
        self.start = start


class StringContainsExpressionNode(BaseStringExpressionNode):

    def __init__(self, operator: str, operand: Any, substring: Any):
        self.operator = operator
        self.operand = operand
        self.substring = substring



substring, prefix, suffix, old, new, start, length, pattern, replacement

class StringLogicalExpressionNode(ExpressionNode):
    """
    Node representing logical string operations (UPPER, LOWER, TRIM, SUBSTRING, etc.).
    """

    def __init__(self, operator: str, operand: Any, *args, **kwargs):
        """
        Initialize string expression node.

        Args:
            operator: String operator (from CONST_EXPRESSION_STRING_OPERATORS)
            operand: The string expression to operate on
            *args: Additional positional arguments (e.g., start, end for substring)
            **kwargs: Additional keyword arguments
        """
        self.operator = operator
        self.operand = operand
        self.args = args
        self.kwargs = kwargs



class StringIterableExpressionNode(ExpressionNode):
    """
    Node representing iterable string operations (CONCAT).


    """


    def __init__(self, operator: str, *operands: Any):
        """
        Args:
            operator: String operator (from CONST_EXPRESSION_STRING_OPERATORS)
            operand: The string expression to operate on
        """
        self.operator = operator
        self.operands = operands
