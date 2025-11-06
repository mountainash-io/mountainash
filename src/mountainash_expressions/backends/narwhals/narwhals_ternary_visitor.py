# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
Narwhals Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""
from __future__ import annotations

from typing import Callable, Any
from functools import reduce

import narwhals as nw
# from numpy import add

from ...core.constants import CONST_TERNARY_LOGIC_VALUES
from ...core.logic import LogicalExpressionNode
from ...core.visitor import TernaryExpressionVisitor

from . import NarwhalsBackendVisitorMixin

# from .value_mappings import DEFAULT_TERNARY_MAPPER, TernaryValueMapper


class NarwhalsTernaryExpressionVisitor(NarwhalsBackendVisitorMixin, TernaryExpressionVisitor):
    """Ternary-aware Narwhals visitor with lambda-based operations following boolean pattern."""


    def __init__(self):
        pass


    # ===============
    # Unary Booleanise Operations
    # ===============

    def _T_is_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)

    def _T_is_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)

    def _T_is_unknown(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)


    def _T_maybe_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))

    def _T_maybe_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN), nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))

    def _T_is_known(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))


    # ===============
    # Comparison Operations
    # ===============

    # Ternary Comparisons

    def _T_eq(self, LHS: Any, RHS: Any) -> nw.Expr:

        return  nw.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
                    nw.when(LHS == RHS).then(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )


    def _T_ne(self, LHS: Any, RHS: Any) -> nw.Expr:
        return  nw.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
                    nw.when(LHS != RHS).then(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _T_gt(self, LHS: Any, RHS: Any) -> nw.Expr:
        return  nw.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
                    nw.when(LHS > RHS).then(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _T_lt(self, LHS: Any, RHS: Any) -> nw.Expr:
        return  nw.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
                    nw.when(LHS < RHS).then(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _T_ge(self, LHS: Any, RHS: Any) -> nw.Expr:
        return  nw.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
                    nw.when(LHS >= RHS).then(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _T_le(self, LHS: Any, RHS: Any) -> nw.Expr:
        return  nw.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
                    nw.when(LHS <= RHS).then(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _T_in(self, LHS: Any, RHS: Any) -> nw.Expr:

        RHS_as_list = list(RHS) if not isinstance(RHS, list) else RHS # Ensure it's a list

        return  nw.when(
                    self._is_unknown_value(LHS)).then(
                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
                    nw.when(LHS.is_in(RHS_as_list)).then(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                        nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )


    # # Unary Comparisons -
    # # TODO: These need rearranging! As Null == Unknown!
    # def _is_null(self, LHS: Any) -> nw.Expr:
    #     return  nw.when(
    #                 LHS.is_null()).then(
    #                 nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
    #                 nw.when(self._is_unknown_value(LHS)).then(
    #                     nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
    #                     nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
    #             )

    # def _not_null(self, LHS: Any) -> nw.Expr:
    #     return  nw.when(
    #                 LHS.is_not_null()).then(
    #                 nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
    #                 nw.when(self._is_unknown_value(LHS)).then(
    #                         nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
    #                         nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
    #             )

    # ===============
    # Logical Operations
    # ===============

    # Unary Operations
    def _T_negate(self,  expression_node: LogicalExpressionNode )-> Callable[[Any], nw.Expr]:
        """Negate an expression. Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        callable_expr = expression_node.operands[0].accept(self)

        return lambda table:     nw.when(callable_expr(table) == nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).then(
                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)).otherwise(
                    nw.when(callable_expr(table) == nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)).then(
                                nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                                nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)))



    def _count_value_direct(self, expressions: list, target_value: int) -> nw.Expr:
        """Helper to count occurrences of a specific value."""
        matches = [
            nw.when(expr == target_value).then(1).otherwise(0)
            for expr in expressions
        ]
        return reduce(lambda x, y: x + y, matches) if matches else nw.lit(0)


    def _T_xor(self, expression_node: LogicalExpressionNode,) -> Callable[[Any], nw.Expr]:
        """XOR: exactly one TRUE using count-based approach (exclusive semantics)."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> nw.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]

            true_count = self._count_value_direct(expressions, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)
            unknown_count = self._count_value_direct(expressions, CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)

            return nw.when(unknown_count > nw.lit(0)).then(
                                nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)).otherwise(
                                nw.when(
                                    true_count == nw.lit(1)).then(
                                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)).otherwise(
                                    nw.lit(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE),
                    )
                )

        return evaluate_expression


    def _T_and(self, expression_node: LogicalExpressionNode) -> Callable[[Any], nw.Expr]:
        """Ternary STRICT_AND using prime multiplication."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> nw.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]
            # For strict AND, the result is simply the minimum value
            return reduce(lambda x, y: nw.min_horizontal(x, y), expressions)

        return evaluate_expression


    def _T_or(self, expression_node: LogicalExpressionNode) -> Callable[[Any], nw.Expr]:
        """Ternary OR using prime multiplication."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> nw.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]
            # For OR, the result is simply the maximum value
            return reduce(lambda x, y: nw.max_horizontal(x, y), expressions)

        return evaluate_expression
