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
import polars as pl

from numpy import add
from .ternary_nodes import TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryLiteralExpressionNode, TernaryExpressionNode
from .ternary_visitor import TernaryExpressionVisitor
from ..core import ExpressionVisitor, ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode
from .constants import TernaryLogicValues
from ..core.backends import PolarsBackendVisitor


# from .constants import TernaryLogicValues
from .value_mappings import DEFAULT_TERNARY_MAPPER, TernaryValueMapper
from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS


class PolarsTernaryExpressionVisitor(PolarsBackendVisitor, TernaryExpressionVisitor):
    """Ternary-aware Polars visitor with lambda-based operations following boolean pattern."""

    _backend = "polars"
    _logic_type = "ternary"


    def __init__(self, ternary_mapper: Optional[TernaryValueMapper] = None, filter_mode: bool = False):
        """Initialize ternary visitor.

        Args:
            ternary_mapper: Custom ternary value mapper for UNKNOWN values
            filter_mode: If True, convert ternary results to boolean for filtering operations
        """
        super().__init__()
        self.ternary_mapper = ternary_mapper or DEFAULT_TERNARY_MAPPER
        self.filter_mode = filter_mode


    # ===============
    # Unary Booleanise Operations
    # ===============

    def _is_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == pl.lit(TernaryLogicValues.TERNARY_TRUE)

    def _is_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == pl.lit(TernaryLogicValues.TERNARY_FALSE)

    def _is_unknown(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)


    def _maybe_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( pl.lit(TernaryLogicValues.TERNARY_TRUE), pl.lit(TernaryLogicValues.TERNARY_UNKNOWN))

    def _maybe_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( pl.lit(TernaryLogicValues.TERNARY_UNKNOWN), pl.lit(TernaryLogicValues.TERNARY_FALSE))

    def _is_known(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) in ( pl.lit(TernaryLogicValues.TERNARY_TRUE), pl.lit(TernaryLogicValues.TERNARY_FALSE))


    # ===============
    # Comparison Operations
    # ===============

    # Ternary Comparisons

    def _eq(self, LHS: Any, RHS: Any) -> pl.Expr:

        return  pl.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                    pl.when(LHS == RHS).then(
                        pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                        pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )


    def _ne(self, LHS: Any, RHS: Any) -> pl.Expr:
        return  pl.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                    pl.when(LHS != RHS).then(
                        pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                        pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )

    def _gt(self, LHS: Any, RHS: Any) -> pl.Expr:
        return  pl.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                    pl.when(LHS > RHS).then(
                        pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                        pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )

    def _lt(self, LHS: Any, RHS: Any) -> pl.Expr:
        return  pl.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                    pl.when(LHS < RHS).then(
                        pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                        pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )

    def _ge(self, LHS: Any, RHS: Any) -> pl.Expr:
        return  pl.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                    pl.when(LHS >= RHS).then(
                        pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                        pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )

    def _le(self, LHS: Any, RHS: Any) -> pl.Expr:
        return  pl.when(
                    self._is_unknown_value(LHS) | self._is_unknown_value(RHS)).then(
                    pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                    pl.when(LHS <= RHS).then(
                        pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                        pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )

    def _in(self, LHS: Any, RHS: Any) -> pl.Expr:

        RHS_as_list = list(RHS) if not isinstance(RHS, list) else RHS # Ensure it's a list

        return  pl.when(
                    self._is_unknown_value(LHS)).then(
                    pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                    pl.when(LHS.is_in(RHS_as_list)).then(
                        pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                        pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )


    # Unary Comparisons -
    # TODO: These need rearranging! As Null == Unknown!
    def _is_null(self, LHS: Any) -> pl.Expr:
        return  pl.when(
                    LHS.is_null()).then(
                    pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                    pl.when(self._is_unknown_value(LHS)).then(
                        pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                        pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )

    def _not_null(self, LHS: Any) -> pl.Expr:
        return  pl.when(
                    LHS.is_not_null()).then(
                    pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                    pl.when(self._is_unknown_value(LHS)).then(
                            pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                            pl.lit(TernaryLogicValues.TERNARY_FALSE))
                )

    # ===============
    # Logical Operations
    # ===============

    # Unary Operations
    def _negate(self,  expression_node: LogicalExpressionNode )-> Callable[[Any], pl.Expr]:
        """Negate an expression. Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        callable_expr = expression_node.operands[0].accept(self)

        return lambda table:     pl.when(callable_expr(table) == pl.lit(TernaryLogicValues.TERNARY_TRUE)).then(
                    pl.lit(TernaryLogicValues.TERNARY_FALSE)).otherwise(
                    pl.when(callable_expr(table) == pl.lit(TernaryLogicValues.TERNARY_FALSE)).then(
                                pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                                pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)))



    def _count_value_direct(self, expressions: list, target_value: int) -> pl.Expr:
        """Helper to count occurrences of a specific value."""
        matches = [
            pl.when(expr == target_value).then(1).otherwise(0)
            for expr in expressions
        ]
        return reduce(lambda x, y: x + y, matches) if matches else pl.lit(0)


    # def _xor_parity(self, expression_node: LogicalExpressionNode) -> Callable[[Any], pl.Expr]:
    #     """XOR_PARITY: odd number TRUE (parity semantics)."""

    #     if not expression_node:
    #         return lambda table: self._format_literal(TernaryLogicValues.TERNARY_UNKNOWN, table)


    #     def evaluate_expression(table: Any) -> pl.Expr:
    #         expressions = [operand.accept(self)(table) for operand in expression_node.operands]

    #         true_count = self._count_value_direct(expressions, TernaryLogicValues.TERNARY_TRUE)
    #         unknown_count = self._count_value_direct(expressions, TernaryLogicValues.TERNARY_UNKNOWN)


    #         return pl.when(unknown_count > pl.lit(0)).then(
    #                 pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
    #                 pl.when(true_count % 2 == pl.lit(1)).then(
    #                         pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
    #                         pl.lit(TernaryLogicValues.TERNARY_FALSE)
    #                     )
    #         )

    #     return evaluate_expression



    def _xor(self, expression_node: LogicalExpressionNode,) -> Callable[[Any], pl.Expr]:
        """XOR: exactly one TRUE using count-based approach (exclusive semantics)."""
        if not expression_node:
            return lambda table: self._format_literal(TernaryLogicValues.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> pl.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]

            true_count = self._count_value_direct(expressions, TernaryLogicValues.TERNARY_TRUE)
            unknown_count = self._count_value_direct(expressions, TernaryLogicValues.TERNARY_UNKNOWN)

            return pl.when(unknown_count > pl.lit(0)).then(
                                pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)).otherwise(
                                pl.when(
                                    true_count == pl.lit(1)).then(
                                    pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
                                    pl.lit(TernaryLogicValues.TERNARY_FALSE),
                    )
                )

        return evaluate_expression





    # def _and_optimistic(self, expression_node: LogicalExpressionNode) -> Callable[[Any], pl.Expr]:
    #     """Ternary Optimistic AND using prime multiplication."""

    #     if not expression_node:
    #         return lambda table: self._format_literal(TernaryLogicValues.TERNARY_UNKNOWN, table)


    #     def evaluate_expression(table: Any) -> pl.Expr:
    #         expressions = [operand.accept(self)(table) for operand in expression_node.operands]
    #         max_val = reduce(lambda x, y: pl.max_horizontal(x, y), expressions)
    #         min_val = reduce(lambda x, y: pl.min_horizontal(x, y), expressions)

    #         return pl.when(
    #             (max_val == pl.lit(TernaryLogicValues.TERNARY_TRUE)) & (min_val >= pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)) ).then(
    #                                 pl.lit(TernaryLogicValues.TERNARY_TRUE)).otherwise(
    #                                 pl.when( max_val == pl.lit(TernaryLogicValues.TERNARY_FALSE)).then(
    #                                             pl.lit(TernaryLogicValues.TERNARY_FALSE)).otherwise(
    #                                             pl.lit(TernaryLogicValues.TERNARY_UNKNOWN)
    #                                 )
    #         )

    #     return evaluate_expression


    def _and(self, expression_node: LogicalExpressionNode) -> Callable[[Any], pl.Expr]:
        """Ternary STRICT_AND using prime multiplication."""
        if not expression_node:
            return lambda table: self._format_literal(TernaryLogicValues.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> pl.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]
            # For strict AND, the result is simply the minimum value
            return reduce(lambda x, y: pl.min_horizontal(x, y), expressions)

        return evaluate_expression


    def _or(self, expression_node: LogicalExpressionNode) -> Callable[[Any], pl.Expr]:
        """Ternary OR using prime multiplication."""
        if not expression_node:
            return lambda table: self._format_literal(TernaryLogicValues.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> pl.Expr:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]
            # For OR, the result is simply the maximum value
            return reduce(lambda x, y: pl.max_horizontal(x, y), expressions)

        return evaluate_expression
