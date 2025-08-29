from typing import Callable, List, Dict, Any
from functools import reduce

import pandas as pd

from . import BooleanExpressionVisitor, BooleanExpressionNode, BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanLiteralExpressionNode
from ..core import ExpressionVisitor, ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode
from ..core.backends import PandasBackendVisitor

from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS

class PandasBooleanExpressionVisitor(PandasBackendVisitor, BooleanExpressionVisitor):



    # ===============
    # Comparison Operations
    # ===============

    # Binary Comparisons

    def _eq(self, LHS: Any, RHS: Any) -> Callable:
        return LHS == RHS

    def _ne(self, LHS: Any, RHS: Any) -> Callable:
        return LHS != RHS

    def _gt(self, LHS: Any, RHS: Any) -> Callable:
        return LHS > RHS

    def _lt(self, LHS: Any, RHS: Any) -> Callable:
        return LHS < RHS

    def _ge(self, LHS: Any, RHS: Any) -> Callable:
        return LHS >= RHS

    def _le(self, LHS: Any, RHS: Any) -> Callable:
        return LHS <= RHS

    def _in(self, LHS: Any, RHS: Any) -> Callable:
        RHS_as_list = list(RHS) if not isinstance(RHS, list) else RHS # Ensure it's a list
        return LHS.isin(RHS_as_list)


    # Unary Comparisons
    def _is_null(self, LHS: Any) -> Callable:
        return LHS.isnull()

    def _not_null(self, LHS: Any) -> Callable:
        return LHS.notnull()



    # ===============
    # Logical Operations
    # ===============

    def _is_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == True

    def _is_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == False


    # Unary Operations
    def _negate(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Negate an expression. Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: ~expression_node.operands[0].accept(self)(table)


    # N-ary Operations
    def _and(self, expression_node: LogicalExpressionNode) -> Callable:
        """Logical AND: all operands must be TRUE."""
        return lambda table: self._combine(table, expression_node.operands, lambda x, y: x & y)

    def _or(self, expression_node: LogicalExpressionNode) -> Callable:
        """Logical OR: at least one operand must be TRUE."""
        return lambda table: self._combine(table, expression_node.operands, lambda x, y: x | y)

    def _xor_exclusive(self, expression_node: LogicalExpressionNode) -> Callable:
        """Boolean exclusive XOR: exactly one operand must be TRUE."""

        # Use reduce pattern: convert booleans to integers, sum them, check if == 1
        combine_func = lambda x, y: x.astype(int) + y.astype(int)
        return lambda table: self._combine(table, expression_node.operands, combine_func) == 1

    def _xor_parity(self, expression_node: LogicalExpressionNode) -> Callable:
        """Boolean parity XOR: odd number of operands must be TRUE."""

        # Use reduce pattern: convert booleans to integers, sum them, check if odd
        combine_func = lambda x, y: x.astype(int) + y.astype(int)
        return lambda table: self._combine(table, expression_node.operands, combine_func) % 2 == 1
