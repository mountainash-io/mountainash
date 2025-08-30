# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
Pandas Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""

from typing import Callable, Any, Optional, List
import ibis
# from functools import reduce
import pandas as pd
import numpy as np

from ...core.constants import CONST_VISITOR_BACKENDS, CONST_TERNARY_LOGIC_VALUES
from ...core.logic import LogicalExpressionNode
from ...core.visitor import TernaryExpressionVisitor

from . import PandasBackendVisitorMixin



class PandasTernaryExpressionVisitor(PandasBackendVisitorMixin, TernaryExpressionVisitor):
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

        return lambda table: expression_node.operands[0].accept(self)(table) == CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE

    def _is_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE

    def _is_unknown(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN


    def _maybe_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)

    def _maybe_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)

    def _is_known(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)


    # ===============
    # Comparison Operations
    # ===============

    # Ternary Comparisons

    def _eq(self, LHS: Any, RHS: Any) -> pd.Series:

        return  pd.Series(np.where(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
                    np.where(LHS == RHS, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)


    def _ne(self, LHS: Any, RHS: Any) -> pd.Series:

        return  pd.Series(np.where(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
                    np.where(LHS != RHS, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)


    def _gt(self, LHS: Any, RHS: Any) -> pd.Series:

        return  pd.Series(np.where(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
                    np.where(LHS > RHS, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)


    def _lt(self, LHS: Any, RHS: Any) -> pd.Series:

        return  pd.Series(np.where(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
                    np.where(LHS < RHS, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)


    def _ge(self, LHS: Any, RHS: Any) -> pd.Series:

        return  pd.Series(np.where(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
                    np.where(LHS >= RHS, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)



    def _le(self, LHS: Any, RHS: Any) -> pd.Series:

        return  pd.Series(np.where(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
                    np.where(LHS <= RHS, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)

    def _in(self, LHS: Any, RHS: Any) -> pd.Series:

        RHS_as_list = list(RHS) if not isinstance(RHS, list) else RHS # Ensure it's a list

        return  pd.Series(np.where(
                    self._is_unknown_value(LHS),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
                    np.where(LHS.isin(RHS_as_list), CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)



    # Unary Comparisons -
    # TODO: These need rearranging! As Null == Unknown!
    def _is_null(self, LHS: Any) -> pd.Series:

        return  pd.Series(np.where(
                    LHS.isna(),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE,
                    np.where(self._is_unknown_value(LHS), CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)



    def _not_null(self, LHS: Any) -> pd.Series:

        return  pd.Series(np.where(
                    LHS.notna(),
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE,
                    np.where(self._is_unknown_value(LHS), CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)
                ), index=LHS.index)

    # ===============
    # Logical Operations
    # ===============

    # Unary Operations
    def _negate(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Negate an expression. Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        callable_expr = expression_node.operands[0].accept(self)

        return lambda table: pd.Series(np.where(
                    callable_expr(table) == CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE,
                    CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE,
                    np.where(callable_expr(table) == CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE,
                                CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE,
                                CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))
        )


    def _count_value_direct(self, series: List[pd.Series], target_value: int) -> pd.Series:
        """Helper to count occurrences of a specific value."""

        stacked_series= pd.concat(series, axis=1)
        matches = (stacked_series == target_value).sum(axis=1)

        return matches


    # def _xor_parity(self, expression_node: LogicalExpressionNode) -> Callable:
    #     """XOR_PARITY: odd number TRUE (parity semantics)."""

    #     if not expression_node:
    #         return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


    #     def evaluate_expression(table: Any) -> pd.Series:

    #         series = [operand.accept(self)(table) for operand in expression_node.operands]

    #         true_count = self._count_value_direct(series, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)
    #         unknown_count = self._count_value_direct(series, CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)

    #         return pd.Series(np.where(
    #                         unknown_count > 0,
    #                         CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
    #                         np.where(
    #                                 true_count % 2 == 1,
    #                                 CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE,
    #                                 CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE,
    #                     )
    #         ))

    #     return evaluate_expression



    def _xor(self, expression_node: LogicalExpressionNode,) -> Callable:
        """XOR: exactly one TRUE using count-based approach (exclusive semantics)."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> pd.Series:

            series = [operand.accept(self)(table) for operand in expression_node.operands]

            true_count = self._count_value_direct(series, CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)
            unknown_count = self._count_value_direct(series, CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)


            return pd.Series(np.where(
                            unknown_count > 0,
                            CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN,
                            np.where(
                                    true_count == 1,
                                    CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE,
                                    CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE,
                        )
            ))


        return evaluate_expression





    # def _and_optimistic(self, expression_node: LogicalExpressionNode) -> Callable:
    #     """Ternary Optimistic AND using prime multiplication."""

    #     if not expression_node:
    #         return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


    #     def evaluate_expression(table: Any) -> pd.Series:

    #         series = [operand.accept(self)(table) for operand in expression_node.operands]

    #         stacked_series= pd.concat(series, axis=1)
    #         max_val = stacked_series.max(axis=1)
    #         min_val = stacked_series.min(axis=1)

    #         return pd.Series(np.where(
    #             (max_val == CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE) & (min_val >= CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
    #                                 CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE,
    #                                 np.where( max_val == CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE,
    #                                             CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE,
    #                                             CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN
    #                                 )
    #         ))



    #     return evaluate_expression


    def _and(self, expression_node: LogicalExpressionNode) -> Callable:
        """Ternary STRICT_AND using prime multiplication."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> pd.Series:

            series = [operand.accept(self)(table) for operand in expression_node.operands]
            stacked_series= pd.concat(series, axis=1)
            print(stacked_series)


            min_val = stacked_series.min(axis=1)
            print(min_val)

            # For strict AND, the result is simply the minimum value
            return min_val

        return evaluate_expression


    def _or(self, expression_node: LogicalExpressionNode) -> Callable:
        """Ternary OR using prime multiplication."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)

        def evaluate_expression(table: Any) -> pd.Series:
            series = [operand.accept(self)(table) for operand in expression_node.operands]
            stacked_series= pd.concat(series, axis=1)

            max_val = stacked_series.max(axis=1)

            # For OR, the result is simply the maximum value
            return max_val

        return evaluate_expression
