# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
PyArrow Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""

from typing import Callable, Any, Optional
from functools import reduce

import pyarrow as pa
import pyarrow.compute as pc

from ...constants import CONST_TERNARY_LOGIC_VALUES
from ...logic.core import LogicalExpressionNode
from ..core import PyArrowBackendVisitor
from . import TernaryExpressionVisitor

# from .value_mappings import DEFAULT_TERNARY_MAPPER


class PyArrowTernaryExpressionVisitor(PyArrowBackendVisitor, TernaryExpressionVisitor ):
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

        return lambda table: pc.equal(expression_node.operands[0].accept(self)(table), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE))

    def _is_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: pc.equal(expression_node.operands[0].accept(self)(table), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))

    def _is_unknown(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: pc.equal(expression_node.operands[0].accept(self)(table), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))


    def _maybe_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: pc.is_in(expression_node.operands[0].accept(self)(table),
            ( pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)))

    def _maybe_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: pc.is_in(expression_node.operands[0].accept(self)(table),
            ( pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)))

    def _is_known(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: pc.is_in(expression_node.operands[0].accept(self)(table),
            ( pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)))



    # ===============
    # Comparison Operations
    # ===============

    # Ternary Comparisons

    def _eq(self, LHS: Any, RHS: Any) -> pa.Array:

        return  pc.if_else(
                    pc.or_(self._is_unknown_value(LHS), self._is_unknown_value(RHS)),
                    pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    pc.if_else(pc.equal(LHS, RHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )


    def _ne(self, LHS: Any, RHS: Any) -> pa.Array:
        return  pc.if_else(
                    pc.or_(self._is_unknown_value(LHS), self._is_unknown_value(RHS)),
                    pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    pc.if_else(pc.not_equal(LHS,RHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _gt(self, LHS: Any, RHS: Any) -> pa.Array:
        return  pc.if_else(
                    pc.or_(self._is_unknown_value(LHS), self._is_unknown_value(RHS)),
                    pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    pc.if_else(pc.greater(LHS ,RHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _lt(self, LHS: Any, RHS: Any) -> pa.Array:
        return  pc.if_else(
                    pc.or_(self._is_unknown_value(LHS), self._is_unknown_value(RHS)),
                    pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    pc.if_else(pc.less(LHS ,RHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _ge(self, LHS: Any, RHS: Any) -> pa.Array:
        return  pc.if_else(
                    pc.or_(self._is_unknown_value(LHS), self._is_unknown_value(RHS)),
                    pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    pc.if_else(pc.greater_equal(LHS ,RHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _le(self, LHS: Any, RHS: Any) -> pa.Array:
        return  pc.if_else(
                    pc.or_(self._is_unknown_value(LHS), self._is_unknown_value(RHS)),
                    pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    pc.if_else(pc.less_equal(LHS ,RHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _in(self, LHS: Any, RHS: Any) -> pa.Array:

        # RHS_as_list = list(RHS) if not isinstance(RHS, list) else RHS # Ensure it's a list

        return  pc.if_else(
                    self._is_unknown_value(LHS),
                    pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                    pc.if_else(pc.is_in(LHS, RHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )


    # Unary Comparisons -
    # TODO: These need rearranging! As Null == Unknown!
    def _is_null(self, LHS: Any) -> pa.Array:
        return  pc.if_else(
                    pc.is_null(LHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                    pc.if_else(self._is_unknown_value(LHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    def _not_null(self, LHS: Any) -> pa.Array:
        return  pc.if_else(
                    pc.is_valid(LHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                    pc.if_else(self._is_unknown_value(LHS), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN), pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE))
                )

    # ===============
    # Logical Operations
    # ===============

    # Unary Operations
    def _negate(self,  expression_node: LogicalExpressionNode )-> Callable[[Any], pa.Array]:
        """Negate an expression. Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        def evaluate_expression(table: Any) -> pa.Array:

            expression = expression_node.operands[0].accept(self)(table)

            return pc.if_else(pc.equal(expression, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)),
                            pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE),
                            pc.if_else(pc.equal(expression, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)),
                                pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                                pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)))

        return evaluate_expression

    def _count_value_direct(self, expressions: list, target_value: int) -> pa.Array:
        """Helper to count occurrences of a specific value."""
        matches = [
            pc.if_else(pc.equal(expr, target_value), pa.scalar(1), pa.scalar(0))
            for expr in expressions
        ]
        return reduce(lambda x, y: pc.add(x, y), matches) if matches else pa.scalar(0)


    # def _xor_parity(self, expression_node: LogicalExpressionNode) -> Callable[[Any], pa.Array]:
    #     """XOR_PARITY: odd number TRUE (parity semantics)."""

    #     if not expression_node:
    #         return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


    #     def evaluate_expression(table: Any) -> pa.Array:
    #         expressions = [operand.accept(self)(table) for operand in expression_node.operands]

    #         true_count = self._count_value_direct(expressions, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE))
    #         unknown_count = self._count_value_direct(expressions, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))


    #         return pc.if_else(pc.greater(unknown_count, pa.scalar(0)),
    #                            pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
    #                            pc.if_else(
    #                                 pc.equal(pc.bit_wise_and(true_count, pa.scalar(1)), pa.scalar(1)),
    #                                 pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
    #                                 pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE),
    #                     )
    #         )

    #     return evaluate_expression



    def _xor(self, expression_node: LogicalExpressionNode,) -> Callable[[Any], pa.Array]:
        """XOR: exactly one TRUE using count-based approach (exclusive semantics)."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> pa.Array:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]

            true_count = self._count_value_direct(expressions, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE))
            unknown_count = self._count_value_direct(expressions, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))

            return pc.if_else(pc.greater(unknown_count, pa.scalar(0)),
                            pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN),
                            pc.if_else(
                                pc.equal(true_count, pa.scalar(1)),
                                pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
                                pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE),
                    )
                )

        return evaluate_expression





    # def _and_optimistic(self, expression_node: LogicalExpressionNode) -> Callable[[Any], pa.Array]:
    #     """Ternary Optimistic AND using prime multiplication."""

    #     if not expression_node:
    #         return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)

    #     def evaluate_expression(table: Any) -> pa.Array:
    #         expressions = [operand.accept(self)(table) for operand in expression_node.operands]
    #         max_val = reduce(lambda x, y: pc.max_element_wise(x, y), expressions)
    #         min_val = reduce(lambda x, y: pc.min_element_wise(x, y), expressions)

    #         return pc.if_else(
    #             pc.and_(pc.equal(max_val, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE)),  pc.greater_equal(min_val, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN))),
    #                                 pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_TRUE),
    #                                 pc.if_else( pc.equal(max_val, pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE)),
    #                                             pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_FALSE),
    #                                             pa.scalar(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN)
    #                                 )
    #         )



        return evaluate_expression


    def _and(self, expression_node: LogicalExpressionNode) -> Callable[[Any], pa.Array]:
        """Ternary STRICT_AND using prime multiplication."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> pa.Array:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]
            # For strict AND, the result is simply the minimum value
            return reduce(lambda x, y: pc.min_element_wise(x, y), expressions)

        return evaluate_expression


    def _or(self, expression_node: LogicalExpressionNode) -> Callable[[Any], pa.Array]:
        """Ternary OR using prime multiplication."""
        if not expression_node:
            return lambda table: self._format_literal(CONST_TERNARY_LOGIC_VALUES.TERNARY_UNKNOWN, table)


        def evaluate_expression(table: Any) -> pa.Array:
            expressions = [operand.accept(self)(table) for operand in expression_node.operands]
            # For OR, the result is simply the maximum value
            return reduce(lambda x, y: pc.max_element_wise(x, y), expressions)

        return evaluate_expression
