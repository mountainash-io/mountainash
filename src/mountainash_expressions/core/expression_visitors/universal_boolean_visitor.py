"""Universal Boolean Expression Visitor using ExpressionSystem.

This module provides a backend-agnostic Boolean logic visitor that works
with any ExpressionSystem implementation through dependency injection.
"""

from __future__ import annotations
from typing import Any, List
from functools import reduce

from ..constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS
from ..expression_system import ExpressionSystem
from ..expression_nodes import ExpressionNode

from .common_mixins import (
    CastExpressionVisitor,
    LiteralExpressionVisitor,
    SourceExpressionVisitor
)

from .boolean_mixins import (
    BooleanCollectionExpressionVisitor,
    BooleanComparisonExpressionVisitor,
    BooleanConstantExpressionVisitor,
    BooleanOperatorsExpressionVisitor,
    BooleanUnaryExpressionVisitor
)

from .arithmetic_mixins import (
    ArithmeticOperatorsExpressionVisitor
)


class UniversalBooleanExpressionVisitor(
    CastExpressionVisitor,
    LiteralExpressionVisitor,
    SourceExpressionVisitor,
    BooleanCollectionExpressionVisitor,
    BooleanComparisonExpressionVisitor,
    BooleanConstantExpressionVisitor,
    BooleanOperatorsExpressionVisitor,
    BooleanUnaryExpressionVisitor,
    ArithmeticOperatorsExpressionVisitor
):
    """
    Universal Boolean logic visitor that works with any backend.

    This visitor is backend-agnostic and uses ExpressionSystem
    for all backend-specific operations. The same visitor instance
    can work with Narwhals, Polars, Pandas, Ibis, or any other
    backend by injecting the appropriate ExpressionSystem.

    Usage:
        from mountainash_expressions.backends.narwhals import NarwhalsExpressionSystem
        from mountainash_expressions.backends.polars import PolarsExpressionSystem

        # Works with Narwhals
        narwhals_visitor = UniversalBooleanExpressionVisitor(NarwhalsExpressionSystem())

        # Works with Polars
        polars_visitor = UniversalBooleanExpressionVisitor(PolarsExpressionSystem())
    """

    def __init__(self, expression_system: ExpressionSystem):
        """
        Initialize with an ExpressionSystem implementation.

        Args:
            expression_system: Backend-specific ExpressionSystem
        """
        self.backend = expression_system

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return the backend type from the injected ExpressionSystem."""
        return self.backend.backend_type

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """Return Boolean logic type."""
        return CONST_LOGIC_TYPES.BOOLEAN

    # ========================================
    # Helper Method: Parameter Processing
    # ========================================

    def _process_operand(self, operand: Any) -> Any:
        """
        Process any operand through centralized type dispatch.

        This method handles ExpressionNodes, strings (column names),
        and raw values (literals), converting them to backend-native
        expressions using the ExpressionSystem.

        Args:
            operand: Can be ExpressionNode, string, raw value, or native expression

        Returns:
            Backend-native expression
        """
        # If it's an ExpressionNode, visit it recursively
        if isinstance(operand, ExpressionNode):
            return operand.accept(self)

        # If it's a string, treat as column reference
        if isinstance(operand, str):
            return self.backend.col(operand)

        # Check if it's already a backend-native expression
        # This is backend-specific, so we do a simple type check
        # If it's not a basic Python type, assume it's already a native expression
        if not isinstance(operand, (int, float, bool, str, type(None), list, tuple, set)):
            return operand

        # Otherwise, treat as literal value
        return self.backend.lit(operand)

    def _process_operands(self, operands: List[Any]) -> List[Any]:
        """Process multiple operands."""
        return [self._process_operand(op) for op in operands]

    # ========================================
    # Comparison Operations
    # ========================================

    def _B_eq(self, left: Any, right: Any) -> Any:
        """Boolean equality: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.eq(left_expr, right_expr)

    def _B_ne(self, left: Any, right: Any) -> Any:
        """Boolean inequality: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.ne(left_expr, right_expr)

    def _B_gt(self, left: Any, right: Any) -> Any:
        """Boolean greater-than: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.gt(left_expr, right_expr)

    def _B_lt(self, left: Any, right: Any) -> Any:
        """Boolean less-than: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.lt(left_expr, right_expr)

    def _B_ge(self, left: Any, right: Any) -> Any:
        """Boolean greater-than-or-equal: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.ge(left_expr, right_expr)

    def _B_le(self, left: Any, right: Any) -> Any:
        """Boolean less-than-or-equal: NULLs treated as False."""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.le(left_expr, right_expr)

    # ========================================
    # Collection Operations
    # ========================================

    def _B_in(self, element: Any, collection: Any) -> Any:
        """Boolean membership test: NULLs treated as False."""
        element_expr = self._process_operand(element)

        # Ensure collection is a list
        if isinstance(collection, (list, tuple, set)):
            collection_list = list(collection)
        else:
            collection_list = [collection]

        return self.backend.is_in(element_expr, collection_list)

    def _B_not_in(self, element: Any, collection: Any) -> Any:
        """Boolean non-membership test: NULLs treated as False."""
        in_result = self._B_in(element, collection)
        return self.backend.not_(in_result)

    # ========================================
    # Null Check Operations
    # ========================================

    def _B_is_null(self, operand: Any) -> Any:
        """Check if operand is NULL."""
        operand_expr = self._process_operand(operand)
        return self.backend.is_null(operand_expr)

    def _B_is_not_null(self, operand: Any) -> Any:
        """Check if operand is not NULL."""
        is_null_result = self._B_is_null(operand)
        return self.backend.not_(is_null_result)

    def _B_not_null(self, operand: Any) -> Any:
        """Alias for _B_is_not_null to match mixin expectations."""
        return self._B_is_not_null(operand)

    # ========================================
    # Arithmetic Operations (Universal - no logic prefix)
    # ========================================

    def _add(self, left: Any, right: Any) -> Any:
        """Addition: left + right"""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.add(left_expr, right_expr)

    def _subtract(self, left: Any, right: Any) -> Any:
        """Subtraction: left - right"""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.subtract(left_expr, right_expr)

    def _multiply(self, left: Any, right: Any) -> Any:
        """Multiplication: left * right"""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.multiply(left_expr, right_expr)

    def _divide(self, left: Any, right: Any) -> Any:
        """Division: left / right"""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.divide(left_expr, right_expr)

    def _modulo(self, left: Any, right: Any) -> Any:
        """Modulo: left % right"""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.modulo(left_expr, right_expr)

    def _power(self, left: Any, right: Any) -> Any:
        """Exponentiation: left ** right"""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.power(left_expr, right_expr)

    def _floor_divide(self, left: Any, right: Any) -> Any:
        """Floor division: left // right"""
        left_expr = self._process_operand(left)
        right_expr = self._process_operand(right)
        return self.backend.floor_divide(left_expr, right_expr)

    # ========================================
    # Unary Logical Operations
    # ========================================

    def _B_is_true(self, operands: List[Any]) -> Any:
        """Check if expression evaluates to TRUE."""
        if not operands:
            raise ValueError("IS_TRUE requires exactly one operand")
        if len(operands) != 1:
            raise ValueError(f"IS_TRUE requires exactly one operand, got {len(operands)}")

        operand_expr = self._process_operand(operands[0])
        true_lit = self.backend.lit(True)
        return self.backend.eq(operand_expr, true_lit)

    def _B_is_false(self, operands: List[Any]) -> Any:
        """Check if expression evaluates to FALSE."""
        if not operands:
            raise ValueError("IS_FALSE requires exactly one operand")
        if len(operands) != 1:
            raise ValueError(f"IS_FALSE requires exactly one operand, got {len(operands)}")

        operand_expr = self._process_operand(operands[0])
        false_lit = self.backend.lit(False)
        return self.backend.eq(operand_expr, false_lit)

    def _B_negate(self, operands: List[Any]) -> Any:
        """Logical NOT operation."""
        if not operands:
            raise ValueError("NOT requires exactly one operand")
        if len(operands) != 1:
            raise ValueError(f"NOT requires exactly one operand, got {len(operands)}")

        operand_expr = self._process_operand(operands[0])
        return self.backend.not_(operand_expr)

    # ========================================
    # N-ary Logical Operations
    # ========================================

    def _B_and(self, operands: List[Any]) -> Any:
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

        # Chain with backend and_ operator using reduce
        return reduce(lambda x, y: self.backend.and_(x, y), expr_list)

    def _B_or(self, operands: List[Any]) -> Any:
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

        # Chain with backend or_ operator using reduce
        return reduce(lambda x, y: self.backend.or_(x, y), expr_list)

    def _B_xor_exclusive(self, operands: List[Any]) -> Any:
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
        # Note: We need a cast method for this
        int_exprs = [self.backend.cast(expr, int) for expr in expr_list]
        sum_expr = reduce(lambda x, y: self.backend.add(x, y), int_exprs)

        # Check if exactly one is true (sum == 1)
        one_lit = self.backend.lit(1)
        return self.backend.eq(sum_expr, one_lit)

    def _B_xor_parity(self, operands: List[Any]) -> Any:
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
        int_exprs = [self.backend.cast(expr, int) for expr in expr_list]
        sum_expr = reduce(lambda x, y: self.backend.add(x, y), int_exprs)

        # Check if sum is odd (sum % 2 == 1)
        two_lit = self.backend.lit(2)
        one_lit = self.backend.lit(1)
        mod_result = self.backend.mod(sum_expr, two_lit)
        return self.backend.eq(mod_result, one_lit)

    # ========================================
    # Constant Operations
    # ========================================

    def _B_always_true(self) -> Any:
        """Return a literal TRUE expression."""
        return self.backend.lit(True)

    def _B_always_false(self) -> Any:
        """Return a literal FALSE expression."""
        return self.backend.lit(False)

    # ========================================
    # Additional Required Methods
    # ========================================

    def _cast(self, value: Any, dtype: Any, **kwargs) -> Any:
        """Cast value to specified type."""
        value_expr = self._process_operand(value)
        return self.backend.cast(value_expr, dtype, **kwargs)

    def _is_reserved_unknown_flag(self, value: Any) -> bool:
        """Check if value is a reserved UNKNOWN flag (for ternary logic)."""
        # For boolean logic, we don't have reserved unknown flags
        # This is primarily for ternary logic support
        return False

    # ========================================
    # Source/Literal Methods (from mixins)
    # ========================================

    def _col(self, column: Any, **kwargs) -> Any:
        """Create a column reference expression."""
        return self.backend.col(column, **kwargs)

    def _lit(self, value: Any) -> Any:
        """Create a literal value expression."""
        return self.backend.lit(value)

    def _is_null(self, operand: Any, **kwargs) -> Any:
        """Check if operand is NULL (for source mixin)."""
        operand_expr = self._process_operand(operand)
        return self.backend.is_null(operand_expr)

    def _is_not_null(self, operand: Any, **kwargs) -> Any:
        """Check if operand is not NULL (for source mixin)."""
        is_null_result = self._is_null(operand)
        return self.backend.not_(is_null_result)

    # ========================================
    # Collection Helper Methods
    # ========================================

    def _as_list(self, value: Any) -> list:
        """Convert value to list if not already a list."""
        return list(value) if not isinstance(value, list) else value

    def _as_set(self, value: Any) -> set:
        """Convert value to set if not already a set."""
        return set(value) if not isinstance(value, set) else value

    # ========================================
    # Compatibility Methods (for BooleanExpressionNode)
    # ========================================
    # These methods bridge the gap between BooleanExpressionNode naming
    # (visit_boolean_*) and mixin naming (visit_*)

    def visit_boolean_comparison_expression(self, expression_node: Any) -> Any:
        """Compatibility wrapper for BooleanComparisonExpressionNode."""
        return self.visit_comparison_expression(expression_node)

    def visit_boolean_logical_expression(self, expression_node: Any) -> Any:
        """Compatibility wrapper for BooleanLogicalExpressionNode."""
        return self.visit_logical_expression(expression_node)

    def visit_boolean_collection_expression(self, expression_node: Any) -> Any:
        """Compatibility wrapper for BooleanCollectionExpressionNode."""
        return self.visit_collection_expression(expression_node)

    def visit_boolean_unary_expression(self, expression_node: Any) -> Any:
        """Compatibility wrapper for BooleanUnaryExpressionNode."""
        return self.visit_unary_expression(expression_node)

    def visit_boolean_conditional_ifelse_expression(self, expression_node: Any) -> Any:
        """Compatibility wrapper for BooleanConditionalIfElseExpressionNode."""
        # Not yet implemented in mixins
        raise NotImplementedError("Conditional expressions not yet supported")
