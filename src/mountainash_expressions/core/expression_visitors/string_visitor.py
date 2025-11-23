
from typing import Callable, TYPE_CHECKING, Dict, Any, Literal
from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce

from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS


from ..expression_parameters import ExpressionParameter
from ..expression_system.base import ExpressionSystem
from .expression_visitor import ExpressionVisitor


from ..protocols import ENUM_STRING_OPERATORS, StringVisitorProtocol

from ...types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes import (
    StringExpressionNode,
    StringIterableExpressionNode,
    StringLogicalExpressionNode,
    PatternExpressionNode,
    PatternLogicalExpressionNode
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


    def visit_expression_node(self, node: SupportedStringExpressionNodes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._string_ops, node)
        return op_func(node)


    def visit_string_iterable_expression(self, node: StringIterableExpressionNode) -> SupportedExpressions:
        op_func = self._get_expr_op(self._string_iterable_ops, node)
        return op_func(node)

    def visit_string_logical_expression(self, node: StringLogicalExpressionNode) -> SupportedExpressions:
        op_func = self._get_expr_op(self._string_logical_ops, node)
        return op_func(node)


    def visit_pattern_expression(self, node: PatternExpressionNode) -> SupportedExpressions:
        op_func = self._get_expr_op(self._pattern_ops, node)
        return op_func(node)

    def visit_pattern_logical_expression(self, node: PatternLogicalExpressionNode) -> SupportedExpressions:
        op_func = self._get_expr_op(self._pattern_logical_ops, node)
        return op_func(node)


    # ========================================
    # String Operations
    # ========================================

    def str_upper(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_upper(operand_expr)

    def str_lower(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_lower(operand_expr)

    def str_trim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_trim(operand_expr)

    def str_ltrim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_ltrim(operand_expr)

    def str_rtrim(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_rtrim(operand_expr)


    def str_substring(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_substring(operand_expr)

    def str_length(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_length(operand_expr)

    def str_replace(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_replace(operand_expr)

    def str_split(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_split(operand_expr)


    # ========================================
    # String iterable Operations
    # ========================================

    def str_concat(self, node: StringIterableExpressionNode) -> SupportedExpressions:
        """
        String concatenate all operands
        """

        expr_list = [ ExpressionParameter(operand).to_native_expression() for operand in node.operands ]

        return self.backend.str_concat(expr_list)

    # ========================================
    # String Logical Operations
    # ========================================

    def str_contains(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""


        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_contains(operand_expr, node.value)


    def str_starts_with(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_starts_with(operand_expr, node.value)


    def str_ends_with(self, node: StringExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.str_ends_with(operand_expr, node.value)

    # ========================================
    # String Pattern  Operations
    # ========================================

    def pat_regex_replace(self, node: PatternExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""


        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.pat_regex_replace(operand_expr, node.value)



    # ========================================
    # String Pattern Logical Operations
    # ========================================

    def pat_like(self, node: PatternLogicalExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.pat_like(operand_expr, node.value)


    def pat_regex_match(self, node: PatternLogicalExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.pat_regex_match(operand_expr, node.value)


    def pat_regex_contains(self, node: PatternLogicalExpressionNode) -> SupportedExpressions:
        """Create a literal value expression."""

        operand_expr =  ExpressionParameter(node.operand).to_native_expression()
        return self.backend.pat_regex_contains(operand_expr, node.value)
