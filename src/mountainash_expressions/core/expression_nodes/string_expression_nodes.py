"""
String expression nodes for the expression AST.

Consolidated node types:
- StringExpressionNode: Unary operations (UPPER, LOWER, TRIM, LENGTH)
- StringPatternNode: Binary operations with a pattern argument
- StringReplaceNode: Replace operations (pattern + replacement)
- StringSliceNode: Substring/slice operations (offset + length)
- StringConcatNode: N-ary concatenation
"""

from __future__ import annotations
from typing import Any, List, Optional, TYPE_CHECKING
from pydantic import Field
from .base_expression_node import ExpressionNode
from ..protocols import ENUM_STRING_OPERATORS


if TYPE_CHECKING:
    from ..expression_visitors import StringExpressionVisitor


class BaseStringExpressionNode(ExpressionNode):
    """
    Base class for all string expression nodes.

    String operations return string values (or integers for LENGTH) and are
    universal across all logic systems.
    """

    operator: ENUM_STRING_OPERATORS = Field()

    def accept(self, visitor: StringExpressionVisitor) -> Any:
        return visitor.visit_expression_node(self)

    def eval(self, dataframe: Any) -> Any:
        from ..expression_visitors import ExpressionVisitorFactory
        backend_type = ExpressionVisitorFactory._identify_backend(dataframe)
        expression_system = ExpressionVisitorFactory._expression_systems_registry[backend_type]()
        visitor = ExpressionVisitorFactory.get_visitor_for_node(self, expression_system)
        return visitor.visit_expression_node(self)


class StringExpressionNode(BaseStringExpressionNode):
    """
    Node for unary string operations.

    Used for: UPPER, LOWER, TRIM, LTRIM, RTRIM, LENGTH, REVERSE, etc.

    These operations take only the string operand with no additional arguments.
    """

    operand: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any):
        super().__init__(
            operator=operator,
            operand=operand
        )


class StringPatternNode(BaseStringExpressionNode):
    """
    Node for string operations with a pattern/substring argument.

    Used for: STARTSWITH, ENDSWITH, CONTAINS, LIKE, REGEX_MATCH,
              SPLIT, FIND, STRIP (with chars), PAD, ZFILL, etc.

    The 'pattern' field is a generic name for the second argument which
    may semantically be a prefix, suffix, substring, regex pattern,
    separator, padding character, etc. depending on the operator.
    """

    operand: Any = Field()
    pattern: Any = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, operand: Any, pattern: Any):
        super().__init__(
            operator=operator,
            operand=operand,
            pattern=pattern
        )


class StringReplaceNode(BaseStringExpressionNode):
    """
    Node for string replacement operations.

    Used for: REPLACE, REGEX_REPLACE

    Takes a pattern to find and a replacement string.
    """

    operand: Any = Field()
    pattern: Any = Field()
    replacement: Any = Field()

    def __init__(
        self,
        operator: ENUM_STRING_OPERATORS,
        operand: Any,
        pattern: Any,
        replacement: Any
    ):
        super().__init__(
            operator=operator,
            operand=operand,
            pattern=pattern,
            replacement=replacement
        )


class StringSliceNode(BaseStringExpressionNode):
    """
    Node for substring/slice operations.

    Used for: SUBSTRING, SLICE, HEAD, TAIL

    Takes an offset and optional length for extracting substrings.
    """

    operand: Any = Field()
    offset: Any = Field()
    length: Optional[Any] = Field(default=None)

    def __init__(
        self,
        operator: ENUM_STRING_OPERATORS,
        operand: Any,
        offset: Any,
        length: Any = None
    ):
        super().__init__(
            operator=operator,
            operand=operand,
            offset=offset,
            length=length
        )


class StringConcatNode(BaseStringExpressionNode):
    """
    Node for string concatenation.

    Used for: CONCAT

    Takes multiple operands to concatenate together.
    """

    operands: List[Any] = Field()

    def __init__(self, operator: ENUM_STRING_OPERATORS, *operands: Any):
        super().__init__(
            operator=operator,
            operands=list(operands)
        )


# =============================================================================
# Backwards Compatibility Aliases (deprecated)
# =============================================================================

# These aliases maintain backwards compatibility but should be migrated
StringIterableExpressionNode = StringConcatNode
StringSuffixExpressionNode = StringPatternNode
StringPrefixExpressionNode = StringPatternNode
StringSubstringExpressionNode = StringSliceNode
StringSearchExpressionNode = StringPatternNode
StringPatternExpressionNode = StringPatternNode
StringReplaceExpressionNode = StringReplaceNode
StringPatternReplaceExpressionNode = StringReplaceNode
StringSplitExpressionNode = StringPatternNode
