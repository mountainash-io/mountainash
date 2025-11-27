from __future__ import annotations
from typing import Any, List, Callable, TYPE_CHECKING
from pydantic import Field
from .base_expression_node import ExpressionNode
from ..protocols import ENUM_STRING_OPERATORS
# from ibis.expr.types import s  # Removed - not used and causes import error


if TYPE_CHECKING:
    from ..expression_visitors import StringExpressionVisitor


class BaseStringExpressionNode(ExpressionNode):
    """
    Node representing string operations (UPPER, LOWER, TRIM, SUBSTRING, etc.).

    String operations return string values (or integers for LENGTH) and are universal
    across all logic systems.

    Supports both:
    - Unary operations: UPPER, LOWER, TRIM, LENGTH (just operand)
    - Operations with arguments: SUBSTRING(start, end), REPLACE(old, new), CONCAT(*args)
    """

    operator: ENUM_STRING_OPERATORS = Field()

    def accept(self, visitor: StringExpressionVisitor) -> Any:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> Any:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: StringExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr




class StringExpressionNode(BaseStringExpressionNode):
    operand: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any):
        super().__init__(
            operator=operator,
            operand=operand
        )


class StringIterableExpressionNode(BaseStringExpressionNode):
    operands: List[Any] = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, *operands: Any):
        super().__init__(
            operator=operator,
            operands=list(operands)
        )


class StringSuffixExpressionNode(BaseStringExpressionNode):

    operand: Any = Field()
    suffix: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, suffix:Any):
        super().__init__(
            operator=operator,
            operand = operand,
            suffix = suffix

        )



class StringPrefixExpressionNode(BaseStringExpressionNode):

    operand: Any = Field()
    prefix: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, prefix:Any):
        super().__init__(
            operator=operator,
            operand = operand,
            prefix = prefix
        )

class StringSubstringExpressionNode(BaseStringExpressionNode):
    operand: Any = Field()
    start: Any = Field()
    length: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, start:Any, length:Any):
        super().__init__(
            operator=operator,
            operand = operand,
            start = start,
            length = length
        )


class StringSearchExpressionNode(BaseStringExpressionNode):
    operand: Any = Field()
    substring: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, substring:Any):
        super().__init__(
            operator=operator,
            operand = operand,
            substring = substring
        )

class StringPatternExpressionNode(BaseStringExpressionNode):
    operand: Any = Field()
    pattern: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, pattern:Any):
        super().__init__(
            operator=operator,
            operand = operand,
            pattern = pattern
        )


class StringReplaceExpressionNode(BaseStringExpressionNode):
    operand: Any = Field()
    substring: Any = Field()
    replacement: Any = Field()


    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, substring:Any, replacement: Any):
        super().__init__(
            operator=operator,
            operand = operand,
            substring = substring,
            replacement = replacement
        )

class StringPatternReplaceExpressionNode(BaseStringExpressionNode):
    operand: Any = Field()
    pattern: Any = Field()
    replacement: Any = Field()


    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, pattern:Any, replacement: Any):
        super().__init__(
            operator=operator,
            operand = operand,
            pattern = pattern,
            replacement = replacement
        )


class StringSplitExpressionNode(BaseStringExpressionNode):
    separator: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, separator:Any):
        super().__init__(
            operator=operator,
            operand = operand,
            separator = separator
        )




# class StringIterableExpressionNode(ExpressionNode):
#     """
#     Node representing iterable string operations (CONCAT).
#     """

#     def __init__(self, operator: str, *operands: Any):
#         """
#         Args:
#             operator: String operator (from CONST_EXPRESSION_STRING_OPERATORS)
#             operand: The string expression to operate on
#         """
#         self.operator = operator
#         self.operands = operands
