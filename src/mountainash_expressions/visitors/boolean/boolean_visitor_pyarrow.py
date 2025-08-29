from typing import Callable, List, Dict, Any
from functools import reduce
from typing_extensions import Pattern

import pyarrow as pa
import pyarrow.compute as pc

from . import BooleanExpressionVisitor, BooleanExpressionNode, BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanLiteralExpressionNode
from ..core import ExpressionVisitor, ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode
from ..core.backends import PyArrowBackendVisitor

from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS

class PyArrowBooleanExpressionVisitor(PyArrowBackendVisitor, BooleanExpressionVisitor):


    # ===============
    # Comparison Operations
    # ===============

    # Binary Comparisons

    def _eq(self, LHS: Any, RHS: Any) -> Any:
        return pc.equal(LHS, RHS)

    def _ne(self, LHS: Any, RHS: Any) -> Any:
        return pc.not_equal(LHS, RHS)

    def _gt(self, LHS: Any, RHS: Any) -> Any:
        return pc.greater(LHS, RHS)

    def _lt(self, LHS: Any, RHS: Any) -> Any:
        return pc.less(LHS, RHS)

    def _ge(self, LHS: Any, RHS: Any) -> Any:
        return pc.greater_equal(LHS, RHS)

    def _le(self, LHS: Any, RHS: Any) -> Any:
        return pc.less_equal(LHS, RHS)

    def _in(self, LHS: Any, RHS: Any) -> Any:
        RHS_as_list = list(RHS) if not isinstance(RHS, list) else RHS
        return pc.is_in(LHS, pa.array(RHS_as_list))

    # Unary Comparisons
    def _is_null(self, LHS: Any) -> Any:
        return pc.is_null(LHS)

    def _not_null(self, LHS: Any) -> Any:
        return pc.is_valid(LHS)



    # ===============
    # Logical Operations
    # ===============


    def _is_true(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: pc.equal(expression_node.operands[0].accept(self)(table), pa.scalar(True))

    def _is_false(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Does the expression resolve to true? Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: pc.equal(expression_node.operands[0].accept(self)(table), pa.scalar(False))

    # Unary Operations
    def _negate(self,  expression_node: LogicalExpressionNode )-> Callable:
        """Negate an expression. Only one node."""

        if not expression_node.operands:
            raise ValueError("Cannot perform operations on empty operands list")

        if len(expression_node.operands) != 1:
            raise ValueError("Negation operation requires exactly one operand")

        return lambda table: pc.invert(expression_node.operands[0].accept(self)(table))


    # N-ary Operations
    def _and(self, expression_node: LogicalExpressionNode) -> Callable:
        """Logical AND: all operands must be TRUE."""
        return lambda table: self._combine(table, expression_node.operands, lambda x, y: pc.and_kleene(x, y))

    def _or(self, expression_node: LogicalExpressionNode) -> Callable:
        """Logical OR: at least one operand must be TRUE."""
        return lambda table: self._combine(table, expression_node.operands, lambda x, y: pc.or_kleene(x, y))

    def _xor_exclusive(self, expression_node: LogicalExpressionNode) -> Callable:
        """Boolean exclusive XOR: exactly one operand must be TRUE."""

        combine_func = lambda x, y: pc.add(x.cast(pa.int64()), y.cast(pa.int64()))
        return lambda table: pc.equal(self._combine(table, expression_node.operands, combine_func), pa.scalar(1))


    def _xor_parity(self, expression_node: LogicalExpressionNode) -> Callable:
        """Boolean parity XOR: odd number of operands must be TRUE."""

        combine_func = lambda x, y: pc.add(x.cast(pa.int64()), y.cast(pa.int64()))
        return lambda table: pc.equal( pc.bit_wise_and(self._combine(table, expression_node.operands, combine_func), pa.scalar(1)), pa.scalar(1))
