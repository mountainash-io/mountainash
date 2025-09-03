from typing import Callable, Any

import narwhals as nw


from ...core.logic import LogicalExpressionNode
# from ...core.logic.boolean import  BooleanExpressionNode, BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanLiteralExpressionNode

from ...core.visitor import BooleanExpressionVisitor
from . import NarwhalsBackendVisitorMixin



class NarwhalsBooleanExpressionVisitor(NarwhalsBackendVisitorMixin, BooleanExpressionVisitor):



    # ===============
    # Comparison Operations
    # ===============

    # Binary Comparisons

    def _B_eq(self, LHS: Any, RHS: Any) -> nw.Expr:
        return LHS == RHS

    def _B_ne(self, LHS: Any, RHS: Any) -> nw.Expr:
        return LHS != RHS

    def _B_gt(self, LHS: Any, RHS: Any) -> nw.Expr:
        return LHS > RHS

    def _B_lt(self, LHS: Any, RHS: Any) -> nw.Expr:
        return LHS < RHS

    def _B_ge(self, LHS: Any, RHS: Any) -> nw.Expr:
        return LHS >= RHS

    def _B_le(self, LHS: Any, RHS: Any) -> nw.Expr:
        return LHS <= RHS

    def _B_in(self, LHS: Any, RHS: Any) -> nw.Expr:
        RHS_as_list = list(RHS) if not isinstance(RHS, list) else RHS # Ensure it's a list
        return LHS.is_in(RHS_as_list)


    # Unary Comparisons
    def _B_is_null(self, LHS: Any) -> nw.Expr:
        return LHS.is_null()

    def _B_not_null(self, LHS: Any) -> nw.Expr:
        return LHS.is_not_null()



    # ===============
    # Logical Operations
    # ===============

    def _B_is_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(True)

    def _B_is_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: expression_node.operands[0].accept(self)(table) == nw.lit(False)

    # Unary Operations
    def _B_negate(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Negate an expression. Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: ~expression_node.operands[0].accept(self)(table)


    # N-ary Operations
    def _B_and(self, expression_node: LogicalExpressionNode) -> Callable:
        """Logical AND: all operands must be TRUE."""
        return lambda table: self._combine(table, expression_node.operands, lambda x, y: x & y)

    def _B_or(self, expression_node: LogicalExpressionNode) -> Callable:
        """Logical OR: at least one operand must be TRUE."""
        return lambda table: self._combine(table, expression_node.operands, lambda x, y: x | y)

    def _B_xor_exclusive(self, expression_node: LogicalExpressionNode) -> Callable:
        """Boolean exclusive XOR: exactly one operand must be TRUE."""

        # Use reduce pattern: convert booleans to integers, sum them, check if == 1
        def combine_func(x, y): return x.cast(nw.Int32) + y.cast(nw.Int32)
        return lambda table: self._combine(table, expression_node.operands, combine_func) == nw.lit(1)

    def _B_xor_parity(self, expression_node: LogicalExpressionNode) -> Callable:
        """Boolean parity XOR: odd number of operands must be TRUE."""

        # Use reduce pattern: convert booleans to integers, sum them, check if odd
        def combine_func(x, y): return x.cast(nw.Int32) + y.cast(nw.Int32)

        return lambda table: self._combine(table, expression_node.operands, combine_func) % 2 == nw.lit(1)
