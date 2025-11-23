from __future__ import annotations
from abc import abstractmethod
from typing import Any, List, Callable, Dict, TYPE_CHECKING
from enum import Enum

# from pandas.core.arrays.datetimelike import isin

from ...constants import CONST_LOGIC_TYPES

from .expression_visitor import ExpressionVisitor
from ..expression_parameters import ExpressionParameter
from functools import reduce
from ...types import SupportedExpressions


from ..expression_nodes import ExpressionNode
from ..expression_nodes.boolean_expression_nodes import BooleanIterableExpressionNode, BooleanComparisonExpressionNode, BooleanCollectionExpressionNode, BooleanUnaryExpressionNode, BooleanConstantExpressionNode, SupportedBooleanExpressionNodeTypes

from ..protocols import BooleanVisitorProtocol, ENUM_BOOLEAN_OPERATORS





class BooleanExpressionVisitor(ExpressionVisitor,
                              BooleanVisitorProtocol):

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN


    # ===============
    # Operations Maps
    # ===============

    @property
    def _boolean_ops(self) -> Dict[Enum, Callable]:

        return {
            ENUM_BOOLEAN_OPERATORS.AND:           self.and_,
            ENUM_BOOLEAN_OPERATORS.OR:            self.or_,
            ENUM_BOOLEAN_OPERATORS.XOR:           self.xor_,
            ENUM_BOOLEAN_OPERATORS.XOR_PARITY:    self.xor_parity,

            ENUM_BOOLEAN_OPERATORS.IS_FALSE:          self.is_false,
            ENUM_BOOLEAN_OPERATORS.IS_TRUE:           self.is_true,
            ENUM_BOOLEAN_OPERATORS.NOT:               self.not_,

            ENUM_BOOLEAN_OPERATORS.EQ:          self.eq,
            ENUM_BOOLEAN_OPERATORS.NE:          self.ne,
            ENUM_BOOLEAN_OPERATORS.GT:          self.gt,
            ENUM_BOOLEAN_OPERATORS.LT:          self.lt,
            ENUM_BOOLEAN_OPERATORS.GE:          self.ge,
            ENUM_BOOLEAN_OPERATORS.LE:          self.le,
            ENUM_BOOLEAN_OPERATORS.IS_CLOSE:    self.is_close,
            ENUM_BOOLEAN_OPERATORS.BETWEEN:     self.between,

            ENUM_BOOLEAN_OPERATORS.IS_IN:          self.is_in,
            ENUM_BOOLEAN_OPERATORS.IS_NOT_IN:      self.is_not_in,

            ENUM_BOOLEAN_OPERATORS.ALWAYS_FALSE:     self.always_false,
            ENUM_BOOLEAN_OPERATORS.ALWAYS_TRUE:      self.always_true,
        }


    # ===============
    # Expression Visitor Methods
    # ===============



    # ===============
    # Logical Expressions
    def visit_expression_node(self, node: SupportedBooleanExpressionNodeTypes) -> SupportedExpressions:

        op_func = self._get_expr_op(self._boolean_ops, node)
        return op_func(node)


    # Logical Iterable Operations
    # ===============

    def and_(self, node: BooleanIterableExpressionNode) -> SupportedExpressions:
        """
        Boolean AND: All operands must be TRUE.
        NULLs treated as False in boolean logic.
        """
        # if not node.operands:
        #     raise ValueError("AND requires at least one operand")
        # if len(node.operands) < 2:
        #     raise ValueError(f"AND requires at least 2 operands, got {len(node.operands)}")

        if not isinstance(node, BooleanIterableExpressionNode):
            raise TypeError(f"Expected BooleanIterableExpressionNode, got {type(node)}")

        expr_list = [ ExpressionParameter(operand).to_native_expression() for operand in node.operands ]

        # Chain with backend and_ operator using reduce
        return reduce(lambda x, y: self.backend.and_(x, y), expr_list)

    def or_(self, node: BooleanIterableExpressionNode) -> SupportedExpressions:
        """
        Boolean OR: At least one operand must be TRUE.
        NULLs treated as False in boolean logic.
        """
        # if not node.operands:
        #     raise ValueError("OR requires at least one operand")
        # if len(node.operands) < 2:
        #     raise ValueError(f"OR requires at least 2 operands, got {len(node.operands)}")

        # Process all operands
        expr_list = [ ExpressionParameter(operand).to_native_expression() for operand in node.operands ]

        # Chain with backend or_ operator using reduce
        return reduce(lambda x, y: self.backend.or_(x, y), expr_list)

    def xor_(self, node: BooleanIterableExpressionNode) -> SupportedExpressions:
        """
        Boolean exclusive XOR: Exactly one operand must be TRUE.

        Implementation: Convert booleans to integers, sum them, check if sum == 1
        """
        # if not node.operands:
        #     raise ValueError("XOR_EXCLUSIVE requires at least one operand")
        # if len(node.operands) < 2:
        #     raise ValueError(f"XOR_EXCLUSIVE requires at least 2 operands, got {len(node.operands)}")

        # Process all operands
        expr_list = [ ExpressionParameter(operand).to_native_expression() for operand in node.operands ]

        # Convert to integers and sum
        # Note: We need a cast method for this
        int_exprs = [self.backend.cast(expr, int) for expr in expr_list]
        sum_expr = reduce(lambda x, y: self.backend.add(x, y), int_exprs)

        # Check if exactly one is true (sum == 1)
        one_lit = self.backend.lit(1)
        return self.backend.eq(sum_expr, one_lit)

    def xor_parity(self, node: BooleanIterableExpressionNode) -> SupportedExpressions:
        """
        Boolean parity XOR: Odd number of operands must be TRUE.

        Implementation: Convert booleans to integers, sum them, check if odd
        """
        # if not node.operands:
        #     raise ValueError("XOR_PARITY requires at least one operand")
        # if len(node.operands) < 2:
        #     raise ValueError(f"XOR_PARITY requires at least 2 operands, got {len(node.operands)}")

        # Process all operands
        expr_list = [ ExpressionParameter(operand).to_native_expression() for operand in node.operands ]

        # Convert to integers and sum
        int_exprs = [self.backend.cast(expr, int) for expr in expr_list]
        sum_expr = reduce(lambda x, y: self.backend.add(x, y), int_exprs)

        # Check if sum is odd (sum % 2 == 1)
        two_lit = self.backend.lit(2)
        one_lit = self.backend.lit(1)
        mod_result = self.backend.mod(sum_expr, two_lit)

        return self.backend.eq(mod_result, one_lit)



    # ========================================
    # Unary Logical Operations
    # ========================================

    def is_true(self, node: BooleanUnaryExpressionNode) -> SupportedExpressions:
        """Check if expression evaluates to TRUE."""
        operand_expr = ExpressionParameter(node.operand).to_native_expression()

        true_lit = self.backend.lit(True)
        return self.backend.eq(operand_expr, true_lit)

    def is_false(self, node: BooleanUnaryExpressionNode) -> SupportedExpressions:
        """Check if expression evaluates to FALSE."""

        operand_expr = ExpressionParameter(node.operand).to_native_expression()

        false_lit = self.backend.lit(False)
        return self.backend.eq(operand_expr, false_lit)

    def negate(self, node: BooleanUnaryExpressionNode) -> SupportedExpressions:
        """Logical NOT operation."""

        operand_expr = ExpressionParameter(node.operand).to_native_expression()

        return self.backend.not_(operand_expr)


    # ========================================
    # Boolean Comparison Operations
    # ========================================



    def eq(self, node: BooleanComparisonExpressionNode) -> SupportedExpressions:
        """Boolean equality: NULLs treated as False."""

        left_expr =  ExpressionParameter(node.left).to_native_expression()
        right_expr = ExpressionParameter(node.right).to_native_expression()

        return self.backend.eq(left_expr, right_expr)

    def ne(self, node: BooleanComparisonExpressionNode) -> SupportedExpressions:
        """Boolean inequality: NULLs treated as False."""
        left_expr =  ExpressionParameter(node.left).to_native_expression()
        right_expr = ExpressionParameter(node.right).to_native_expression()
        return self.backend.ne(left_expr, right_expr)

    def gt(self, node: BooleanComparisonExpressionNode) -> SupportedExpressions:
        """Boolean greater-than: NULLs treated as False."""
        left_expr =  ExpressionParameter(node.left).to_native_expression()
        right_expr = ExpressionParameter(node.right).to_native_expression()
        return self.backend.gt(left_expr, right_expr)

    def lt(self, node: BooleanComparisonExpressionNode) -> SupportedExpressions:
        """Boolean less-than: NULLs treated as False."""
        left_expr =  ExpressionParameter(node.left).to_native_expression()
        right_expr = ExpressionParameter(node.right).to_native_expression()
        return self.backend.lt(left_expr, right_expr)

    def ge(self, node: BooleanComparisonExpressionNode) -> SupportedExpressions:
        """Boolean greater-than-or-equal: NULLs treated as False."""
        left_expr =  ExpressionParameter(node.left).to_native_expression()
        right_expr = ExpressionParameter(node.right).to_native_expression()
        return self.backend.ge(left_expr, right_expr)

    def le(self, node: BooleanComparisonExpressionNode) -> SupportedExpressions:
        """Boolean less-than-or-equal: NULLs treated as False."""
        left_expr =  ExpressionParameter(node.left).to_native_expression()
        right_expr = ExpressionParameter(node.right).to_native_expression()
        return self.backend.le(left_expr, right_expr)


    def is_close(self, node: BooleanComparisonExpressionNode) -> SupportedExpressions:
        """Boolean less-than-or-equal: NULLs treated as False."""
        left_expr =  ExpressionParameter(node.left).to_native_expression()
        right_expr = ExpressionParameter(node.right).to_native_expression()
        precision = node.precision
        return self.backend.is_close(left_expr, right_expr, precision)

    def between(self, node: BooleanComparisonExpressionNode) -> SupportedExpressions:
        """Boolean less-than-or-equal: NULLs treated as False."""
        left_expr =  ExpressionParameter(node.left).to_native_expression()
        right_expr = ExpressionParameter(node.right).to_native_expression()
        closed = node.closed

        return self.backend.between(left_expr, right_expr, closed)

    # ========================================
    # Boolean Collection Operations
    # ========================================

    def is_in(self, node: BooleanCollectionExpressionNode) -> SupportedExpressions:
        """Boolean membership test: NULLs treated as False."""
        element_expr = ExpressionParameter(node.element).to_native_expression()

        # Ensure collection is a list
        if isinstance(node.container, (list, tuple, set)):
            collection_list = list(node.container)
        else:
            collection_list = [node.container]

        return self.backend.is_in(element_expr, collection_list)

    def is_not_in(self, node: BooleanCollectionExpressionNode) -> SupportedExpressions:
        """Boolean non-membership test: NULLs treated as False."""
        in_result = self.is_in(node)
        return self.backend.not_(in_result)


    # ========================================
    # Boolean Constant Operations
    # ========================================


    def always_true(self, node: BooleanConstantExpressionNode) -> SupportedExpressions:
        """Return a literal TRUE expression."""
        return self.backend.lit(True)

    def always_false(self, node: BooleanConstantExpressionNode) -> SupportedExpressions:
        """Return a literal FALSE expression."""
        return self.backend.lit(False)
