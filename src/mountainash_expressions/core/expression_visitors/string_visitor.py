from __future__ import annotations


from typing import Callable, TYPE_CHECKING, Dict
from enum import Enum



from ..expression_parameters import ExpressionParameter
from .expression_visitor import ExpressionVisitor


from ..protocols import ENUM_STRING_OPERATORS, StringVisitorProtocol

from ...types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes import (
        StringExpressionNode,
        StringIterableExpressionNode,
        StringSuffixExpressionNode,
        StringPrefixExpressionNode,
        StringSubstringExpressionNode,
        StringSearchExpressionNode,
        StringPatternExpressionNode,
        StringReplaceExpressionNode,
        StringPatternReplaceExpressionNode,
        StringSplitExpressionNode,
        SupportedStringExpressionNodeTypes
)


class StringExpressionVisitor(ExpressionVisitor,
                            StringVisitorProtocol,
):

    # ========================================
    # String Operations
    # ========================================

    @property
    def _string_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_STRING_OPERATORS.STR_UPPER:            self.str_upper,
            ENUM_STRING_OPERATORS.STR_LOWER:            self.str_lower,
            ENUM_STRING_OPERATORS.STR_TRIM:             self.str_trim,
            ENUM_STRING_OPERATORS.STR_LTRIM:            self.str_ltrim,
            ENUM_STRING_OPERATORS.STR_RTRIM:            self.str_rtrim,
            ENUM_STRING_OPERATORS.STR_SUBSTRING:        self.str_substring,
            ENUM_STRING_OPERATORS.STR_LENGTH:           self.str_length,
            ENUM_STRING_OPERATORS.STR_REPLACE:          self.str_replace,

            ENUM_STRING_OPERATORS.STR_CONCAT:           self.str_concat,

            ENUM_STRING_OPERATORS.STR_CONTAINS:         self.str_contains,
            ENUM_STRING_OPERATORS.STR_STARTS_WITH:      self.str_starts_with,
            ENUM_STRING_OPERATORS.STR_ENDS_WITH:        self.str_ends_with,

            ENUM_STRING_OPERATORS.PAT_REGEX_REPLACE:    self.pat_regex_replace,

            ENUM_STRING_OPERATORS.PAT_LIKE:             self.pat_like,
            ENUM_STRING_OPERATORS.PAT_REGEX_MATCH:      self.pat_regex_match,
            ENUM_STRING_OPERATORS.PAT_REGEX_CONTAINS:   self.pat_regex_contains,


        }
    # ========================================
    # Boolean Comparison Operations
    # ========================================


    def visit_expression_node(self, node: SupportedStringExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._string_ops, node)
        return op_func(node)



    # ========================================
    # String Operations
    # ========================================

    def str_upper(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_upper(operand_expr)

    def str_lower(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_lower(operand_expr)

    def str_trim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_trim(operand_expr)

    def str_ltrim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_ltrim(operand_expr)

    def str_rtrim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_rtrim(operand_expr)


    def str_substring(self, node: StringSubstringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_substring(operand_expr, node.start, node.length)

    def str_length(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_length(operand_expr)

    def str_replace(self, node: StringReplaceExpressionNode) -> SupportedExpressions:
        """Replace substring with replacement."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_replace(operand_expr, node.substring, node.replacement)

    def str_split(self, node: StringSplitExpressionNode) -> SupportedExpressions:
        """Split string by separator."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_split(operand_expr, node.separator)


    # ========================================
    # String iterable Operations
    # ========================================

    def str_concat(self, node: StringIterableExpressionNode) -> SupportedExpressions:
        """
        String concatenate all operands
        """

        expr_list = [ ExpressionParameter(operand, expression_system=self.backend).to_native_expression() for operand in node.operands ]

        return self.backend.str_concat(expr_list)

    # ========================================
    # String Logical Operations
    # ========================================

    def str_contains(self, node: StringSearchExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""


        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_contains(operand_expr, node.substring)


    def str_starts_with(self, node: StringPrefixExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_starts_with(operand_expr, node.prefix)


    def str_ends_with(self, node: StringSuffixExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_ends_with(operand_expr, node.suffix)

    # ========================================
    # String Pattern  Operations
    # ========================================

    def pat_regex_replace(self, node: StringPatternReplaceExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""


        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.pat_regex_replace(operand_expr, node.pattern, node.replacement)



    # ========================================
    # String Pattern Logical Operations
    # ========================================

    def pat_like(self, node: StringPatternExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.pat_like(operand_expr, node.pattern)


    def pat_regex_match(self, node: StringPatternExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.pat_regex_match(operand_expr, node.pattern)


    def pat_regex_contains(self, node: StringPatternExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.pat_regex_contains(operand_expr, node.pattern)
