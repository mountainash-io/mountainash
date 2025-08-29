# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
Ibis Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""

from typing import Callable, Any, Optional, List, Literal
import ibis
import ibis.expr.types as ir
from functools import reduce

from ...constants import CONST_TERNARY_LOGIC_VALUES
from ...logic.core import LogicalExpressionNode
# from ...logic.ternary import TernaryExpressionNode, TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryLiteralExpressionNode

from ..core import IbisBackendVisitor
from . import TernaryExpressionVisitor


class IbisTernaryExpressionVisitor(IbisBackendVisitor, TernaryExpressionVisitor):
    """Ternary-aware Ibis visitor with lambda-based operations following boolean pattern."""


    def __init__(self):
        pass

    # ===============
    # Unary Booleanise Operations
    # ===============
    def _is_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)

    def _is_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to false? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)

    def _is_unknown(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to unknown? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)


    def _maybe_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true or unknown? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))

    def _maybe_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to false or unknown? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))

    def _is_known(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true or false? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))



    # ===============
    # Comparison Operations
    # ===============

    # Ternary Comparisons. These are internals that return the CONST_TERNARY_LOGIC_VALUES directly. The calling visitor method will wrap these in a lambda with table parameter.

    def _eq(self, LHS: Any, RHS: Any) -> ir.Expr:

        return  ibis.ifelse(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    ibis.ifelse(LHS == RHS, ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )


    def _ne(self, LHS: Any, RHS: Any) -> ir.Expr:
        return  ibis.ifelse(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    ibis.ifelse(LHS != RHS, ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _gt(self, LHS: Any, RHS: Any) -> ir.Expr:
        return  ibis.ifelse(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    ibis.ifelse(LHS > RHS, ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _lt(self, LHS: Any, RHS: Any) -> ir.Expr:
        return  ibis.ifelse(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    ibis.ifelse(LHS < RHS, ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _ge(self, LHS: Any, RHS: Any) -> ir.Expr:
        return  ibis.ifelse(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    ibis.ifelse(LHS >= RHS, ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _le(self, LHS: Any, RHS: Any) -> ir.Expr:
        return  ibis.ifelse(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    ibis.ifelse(LHS <= RHS, ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _in(self, LHS: Any, RHS: Any) -> ir.Expr:

        RHS_as_list = list(RHS) if not isinstance(RHS, list) else RHS # Ensure it's a list

        return  ibis.ifelse(
                    self._is_unknown_value(LHS),
                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    ibis.ifelse(LHS.isin(RHS_as_list), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )


    # Unary Comparisons -
    # TODO: These need rearranging! As Null == Unknown!
    def _is_null(self, LHS: Any) -> ir.Expr:
        return  ibis.ifelse(
                    LHS.isnull(), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                    ibis.ifelse(self._is_unknown_value(LHS), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _not_null(self, LHS: Any) -> ir.Expr:
        return  ibis.ifelse(
                    LHS.notnull(), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                    ibis.ifelse(self._is_unknown_value(LHS), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN), ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    # ===============
    # Logical Operations
    # ===============

    # Unary Operations
    def _negate(self,  expression_node: LogicalExpressionNode )-> Callable[[Any], ir.Expr]:
        """Negate an expression. Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        callable_expr = expression_node.operands[0].accept(self)

        return lambda table:     ibis.ifelse(callable_expr(table) == ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE),
                    ibis.ifelse(callable_expr(table) == ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE),
                                ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                                ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)))



    def _count_value_direct(self, expressions: list, target_value: int) -> ir.Expr:
        """Helper to count occurrences of a specific value."""
        matches = [
            ibis.case().when(expr == target_value, 1).else_(0).end()
            for expr in expressions
        ]
        return reduce(lambda x, y: x + y, matches) if matches else ibis.literal(0)


    def _xor(self, expression_node: LogicalExpressionNode,) -> Callable[[Any], ir.Expr]:
        """XOR: exactly one TRUE using count-based approach (exclusive semantics)."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> ir.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]

            true_count = self._count_value_direct(expressions, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)
            unknown_count = self._count_value_direct(expressions, CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)

            return ibis.ifelse(unknown_count > ibis.literal(0),
                                ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                                ibis.ifelse(
                                    true_count == ibis.literal(1),
                                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                                    ibis.literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE),
                    )
                )

        return evaluate_expression


    def _and(self, expression_node: LogicalExpressionNode) -> Callable[[Any], ir.Expr]:
        """Ternary AND"""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> ir.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]
            # For strict AND, the result is simply the minimum value
            return reduce(lambda x, y: ibis.least(x, y), expressions)

        return evaluate_expression


    def _or(self, expression_node: LogicalExpressionNode) -> Callable[[Any], ir.Expr]:
        """Ternary OR"""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> ir.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]
            # For OR, the result is simply the maximum value
            return reduce(lambda x, y: ibis.greatest(x, y), expressions)

        return evaluate_expression
