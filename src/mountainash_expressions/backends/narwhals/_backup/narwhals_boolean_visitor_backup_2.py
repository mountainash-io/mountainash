from __future__ import annotations
from typing import Any, List
from functools import reduce

import narwhals as nw

from ...core.expression_nodes import ExpressionNode, LogicalExpressionNode
from ...core.expression_visitors import BooleanExpressionVisitor
from ...core.expression_parameters import ExpressionParameter
from .narwhals_visitor import NarwhalsBackendBaseVisitor

from ...core.expression_visitors.boolean_mixins import (
    BooleanCollectionExpressionVisitor,
    BooleanComparisonExpressionVisitor,
    BooleanConstantExpressionVisitor,
    BooleanOperatorsExpressionVisitor,
    BooleanUnaryExpressionVisitor
)


class NarwhalsBooleanExpressionVisitor(NarwhalsBackendBaseVisitor,
                                        BooleanCollectionExpressionVisitor,
                                        BooleanComparisonExpressionVisitor,
                                        BooleanConstantExpressionVisitor,
                                        BooleanOperatorsExpressionVisitor,
                                        BooleanUnaryExpressionVisitor):
    """
    Narwhals backend implementation for Boolean logic expressions.

    Returns backend expressions (nw.Expr) directly - no Callables.
    Follows the documented architecture from ExpressionSystemRefactoring.
    """

    # ========================================
    # Helper Method: Parameter Processing
    # ========================================

    def _process_operand(self, operand: Any) -> nw.Expr:
        """
        Process any operand through ExpressionParameter.

        This centralized method handles all type dispatch,
        converting any input to a native Narwhals expression.

        Args:
            operand: Can be ExpressionNode, raw value, or nw.Expr

        Returns:
            nw.Expr ready for use in Narwhals operations
        """
        # If already a Narwhals expression, return as-is
        if isinstance(operand, nw.Expr):
            return operand

        # If it's an ExpressionNode, visit it recursively
        if isinstance(operand, ExpressionNode):
            return operand.accept(self)

        # Otherwise, try to convert through parameter system
        # For now, handle basic types directly
        # (Full ExpressionParameter integration can be added later)
        if isinstance(operand, str):
            return self._col(operand)
        else:
            return self._lit(operand)

    def _process_operands(self, operands: List[Any]) -> List[nw.Expr]:
        """Process multiple operands."""
        return [self._process_operand(op) for op in operands]

    # ========================================
    # Comparison Operations
    # ========================================

    def _B_eq(self, left: Any, right: Any) -> nw.Expr:
        """Boolean equality: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return left_expr == right_expr

    def _B_ne(self, left: Any, right: Any) -> nw.Expr:
        """Boolean inequality: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return left_expr != right_expr

    def _B_gt(self, left: Any, right: Any) -> nw.Expr:
        """Boolean greater-than: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return left_expr > right_expr

    def _B_lt(self, left: Any, right: Any) -> nw.Expr:
        """Boolean less-than: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return left_expr < right_expr

    def _B_ge(self, left: Any, right: Any) -> nw.Expr:
        """Boolean greater-than-or-equal: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return left_expr >= right_expr

    def _B_le(self, left: Any, right: Any) -> nw.Expr:
        """Boolean less-than-or-equal: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return left_expr <= right_expr

    # ========================================
    # Collection Operations
    # ========================================

    def _B_in(self, element: Any, collection: Any) -> nw.Expr:
        """Boolean membership test: NULLs treated as False."""
        element_expr = self._process_operand(element)

        # Ensure collection is a list
        if isinstance(collection, (list, tuple, set)):
            collection_list = list(collection)
        else:
            collection_list = [collection]

        return element_expr.is_in(collection_list)

    def _B_not_in(self, element: Any, collection: Any) -> nw.Expr:
        """Boolean non-membership test: NULLs treated as False."""
        return ~self._B_in(element, collection)

    # ========================================
    # Null Check Operations
    # ========================================

    def _B_is_null(self, operand: Any) -> nw.Expr:
        """Check if operand is NULL."""
        operand_expr = self._process_operand(operand)
        return operand_expr.is_null()

    def _B_is_not_null(self, operand: Any) -> nw.Expr:
        """Check if operand is not NULL."""
        operand_expr = self._process_operand(operand)
        return ~operand_expr.is_null()

    # ========================================
    # Unary Logical Operations
    # ========================================

    def _B_is_true(self, operands: List[Any]) -> nw.Expr:
        """Check if expression evaluates to TRUE."""
        if not operands:
            raise ValueError("IS_TRUE requires exactly one operand")
        if len(operands) != 1:
            raise ValueError(f"IS_TRUE requires exactly one operand, got {len(operands)}")

        operand_expr = self._process_operand(operands[0])
        return operand_expr == nw.lit(True)

    def _B_is_false(self, operands: List[Any]) -> nw.Expr:
        """Check if expression evaluates to FALSE."""
        if not operands:
            raise ValueError("IS_FALSE requires exactly one operand")
        if len(operands) != 1:
            raise ValueError(f"IS_FALSE requires exactly one operand, got {len(operands)}")

        operand_expr = self._process_operand(operands[0])
        return operand_expr == nw.lit(False)

    def _B_negate(self, operands: List[Any]) -> nw.Expr:
        """Logical NOT operation."""
        if not operands:
            raise ValueError("NOT requires exactly one operand")
        if len(operands) != 1:
            raise ValueError(f"NOT requires exactly one operand, got {len(operands)}")

        operand_expr = self._process_operand(operands[0])
        return ~operand_expr

    # ========================================
    # N-ary Logical Operations
    # ========================================

    def _B_and(self, operands: List[Any]) -> nw.Expr:
        """
        Boolean AND: All operands must be TRUE.
        NULLs treated as False in boolean logic.
        """
        if not operands:
            raise ValueError("AND requires at least one operand")
        if len(operands) < 2:
            raise ValueError(f"AND requires at least 2 operands, got {len(operands)}")

        # Process all operands
        expr_list = self._process_operands(operands)

        # Chain with & operator using reduce
        return reduce(lambda x, y: x & y, expr_list)

    def _B_or(self, operands: List[Any]) -> nw.Expr:
        """
        Boolean OR: At least one operand must be TRUE.
        NULLs treated as False in boolean logic.
        """
        if not operands:
            raise ValueError("OR requires at least one operand")
        if len(operands) < 2:
            raise ValueError(f"OR requires at least 2 operands, got {len(operands)}")

        # Process all operands
        expr_list = self._process_operands(operands)

        # Chain with | operator using reduce
        return reduce(lambda x, y: x | y, expr_list)

    def _B_xor_exclusive(self, operands: List[Any]) -> nw.Expr:
        """
        Boolean exclusive XOR: Exactly one operand must be TRUE.

        Implementation: Convert booleans to integers, sum them, check if sum == 1
        """
        if not operands:
            raise ValueError("XOR_EXCLUSIVE requires at least one operand")
        if len(operands) < 2:
            raise ValueError(f"XOR_EXCLUSIVE requires at least 2 operands, got {len(operands)}")

        # Process all operands
        expr_list = self._process_operands(operands)

        # Convert to integers and sum
        int_exprs = [expr.cast(nw.Int32) for expr in expr_list]
        sum_expr = reduce(lambda x, y: x + y, int_exprs)

        # Check if exactly one is true (sum == 1)
        return sum_expr == nw.lit(1)

    def _B_xor_parity(self, operands: List[Any]) -> nw.Expr:
        """
        Boolean parity XOR: Odd number of operands must be TRUE.

        Implementation: Convert booleans to integers, sum them, check if odd
        """
        if not operands:
            raise ValueError("XOR_PARITY requires at least one operand")
        if len(operands) < 2:
            raise ValueError(f"XOR_PARITY requires at least 2 operands, got {len(operands)}")

        # Process all operands
        expr_list = self._process_operands(operands)

        # Convert to integers and sum
        int_exprs = [expr.cast(nw.Int32) for expr in expr_list]
        sum_expr = reduce(lambda x, y: x + y, int_exprs)

        # Check if sum is odd (sum % 2 == 1)
        return (sum_expr % nw.lit(2)) == nw.lit(1)

    # ========================================
    # Constant Operations
    # ========================================

    def _B_always_true(self) -> nw.Expr:
        """Return a literal TRUE expression."""
        return nw.lit(True)

    def _B_always_false(self) -> nw.Expr:
        """Return a literal FALSE expression."""
        return nw.lit(False)

    # ========================================
    # Additional Required Methods
    # ========================================

    def _B_not_null(self, operand: Any) -> nw.Expr:
        """Alias for _B_is_not_null to match mixin expectations."""
        return self._B_is_not_null(operand)

    def _cast(self, value: Any, type: Any, **kwargs) -> nw.Expr:
        """Cast value to specified type."""
        value_expr = self._process_operand(value)
        return value_expr.cast(type, **kwargs)

    def _is_reserved_unknown_flag(self, value: Any) -> bool:
        """Check if value is a reserved UNKNOWN flag (for ternary logic)."""
        # For boolean logic, we don't have reserved unknown flags
        # This is primarily for ternary logic support
        return False
