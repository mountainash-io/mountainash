"""String expression visitor for evaluating string operations."""

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
        StringPatternNode,
        StringReplaceNode,
        StringSliceNode,
        StringConcatNode,
    )
    from ..expression_nodes.types import SupportedStringExpressionNodeTypes


class StringExpressionVisitor(ExpressionVisitor, StringVisitorProtocol):
    """Visitor for string expression nodes."""

    @property
    def _string_ops(self) -> Dict[Enum, Callable]:
        return {
            # Unary operations (StringExpressionNode)
            ENUM_STRING_OPERATORS.STR_UPPER:            self.str_upper,
            ENUM_STRING_OPERATORS.STR_LOWER:            self.str_lower,
            ENUM_STRING_OPERATORS.STR_TRIM:             self.str_trim,
            ENUM_STRING_OPERATORS.STR_LTRIM:            self.str_ltrim,
            ENUM_STRING_OPERATORS.STR_RTRIM:            self.str_rtrim,
            ENUM_STRING_OPERATORS.STR_LENGTH:           self.str_length,

            # Pattern operations (StringPatternNode)
            ENUM_STRING_OPERATORS.STR_CONTAINS:         self.str_contains,
            ENUM_STRING_OPERATORS.STR_STARTS_WITH:      self.str_starts_with,
            ENUM_STRING_OPERATORS.STR_ENDS_WITH:        self.str_ends_with,
            ENUM_STRING_OPERATORS.PAT_LIKE:             self.pat_like,
            ENUM_STRING_OPERATORS.PAT_REGEX_MATCH:      self.pat_regex_match,
            ENUM_STRING_OPERATORS.PAT_REGEX_CONTAINS:   self.pat_regex_contains,

            # Replace operations (StringReplaceNode)
            ENUM_STRING_OPERATORS.STR_REPLACE:          self.str_replace,
            ENUM_STRING_OPERATORS.PAT_REGEX_REPLACE:    self.pat_regex_replace,

            # Slice operations (StringSliceNode)
            ENUM_STRING_OPERATORS.STR_SUBSTRING:        self.str_substring,

            # Concat operations (StringConcatNode)
            ENUM_STRING_OPERATORS.STR_CONCAT:           self.str_concat,
        }

    def visit_expression_node(self, node: SupportedStringExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._string_ops, node)
        return op_func(node)

    # ========================================
    # Unary String Operations (StringExpressionNode)
    # ========================================

    def str_upper(self, node: StringExpressionNode) -> SupportedExpressions:
        """Convert string to uppercase."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_upper(operand_expr)

    def str_lower(self, node: StringExpressionNode) -> SupportedExpressions:
        """Convert string to lowercase."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_lower(operand_expr)

    def str_trim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Trim whitespace from both ends."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_trim(operand_expr)

    def str_ltrim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Trim whitespace from left side."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_ltrim(operand_expr)

    def str_rtrim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Trim whitespace from right side."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_rtrim(operand_expr)

    def str_length(self, node: StringExpressionNode) -> SupportedExpressions:
        """Get string length."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_length(operand_expr)

    # ========================================
    # Pattern Operations (StringPatternNode)
    # ========================================

    def str_contains(self, node: StringPatternNode) -> SupportedExpressions:
        """Check if string contains pattern."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_contains(operand_expr, node.pattern)

    def str_starts_with(self, node: StringPatternNode) -> SupportedExpressions:
        """Check if string starts with pattern."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_starts_with(operand_expr, node.pattern)

    def str_ends_with(self, node: StringPatternNode) -> SupportedExpressions:
        """Check if string ends with pattern."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_ends_with(operand_expr, node.pattern)

    def pat_like(self, node: StringPatternNode) -> SupportedExpressions:
        """SQL LIKE pattern match."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.pat_like(operand_expr, node.pattern)

    def pat_regex_match(self, node: StringPatternNode) -> SupportedExpressions:
        """Regex pattern match (full string)."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.pat_regex_match(operand_expr, node.pattern)

    def pat_regex_contains(self, node: StringPatternNode) -> SupportedExpressions:
        """Regex pattern contains (partial match)."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.pat_regex_contains(operand_expr, node.pattern)

    # ========================================
    # Replace Operations (StringReplaceNode)
    # ========================================

    def str_replace(self, node: StringReplaceNode) -> SupportedExpressions:
        """Replace substring with replacement."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_replace(operand_expr, node.pattern, node.replacement)

    def pat_regex_replace(self, node: StringReplaceNode) -> SupportedExpressions:
        """Regex pattern replace."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.pat_regex_replace(operand_expr, node.pattern, node.replacement)

    # ========================================
    # Slice Operations (StringSliceNode)
    # ========================================

    def str_substring(self, node: StringSliceNode) -> SupportedExpressions:
        """Extract substring."""
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.str_substring(operand_expr, node.offset, node.length)

    # ========================================
    # Concat Operations (StringConcatNode)
    # ========================================

    def str_concat(self, node: StringConcatNode) -> SupportedExpressions:
        """Concatenate multiple strings."""
        expr_list = [
            ExpressionParameter(operand, expression_system=self.backend).to_native_expression()
            for operand in node.operands
        ]
        return self.backend.str_concat(expr_list)
