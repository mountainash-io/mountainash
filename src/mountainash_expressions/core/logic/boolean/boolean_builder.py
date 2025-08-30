from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional

from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS
# from ..core import ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode
from .boolean_nodes import BooleanExpressionNode, BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanLiteralExpressionNode

class BooleanExpressionBuilder:


    # =====================================
    #####  Actual Implementations ####
    # =====================================

    @classmethod
    def always_true(cls) -> BooleanLogicalExpressionNode:
        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_TRUE, [])

    @classmethod
    def always_false(cls) -> BooleanLogicalExpressionNode:
        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_FALSE, [])

    # =====================================
    # Column to Value comparisons
    # =====================================
    @classmethod
    def equals(cls, column: str, value: Any) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.EQ, column, value)

    @classmethod
    def not_equals(cls, column: str, value: Any) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NE, column, value)

    @classmethod
    def greater_than(cls, column: str, value: Union[int, float]) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GT, column, value)

    @classmethod
    def less_than(cls, column: str, value: Union[int, float]) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LT, column, value)

    @classmethod
    def greater_than_or_equal(cls, column: str, value: Union[int, float]) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GE, column, value)

    @classmethod
    def less_than_or_equal(cls, column: str, value: Union[int, float]) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LE, column, value)


    @classmethod
    def between(cls, column: str, lower: Union[int, float], upper: Union[int, float], lower_eq: bool=True, upper_eq: bool = True) -> BooleanLogicalExpressionNode:

        lower_operator = CONST_EXPRESSION_LOGIC_OPERATORS.GE if lower_eq else CONST_EXPRESSION_LOGIC_OPERATORS.GT
        upper_operator = CONST_EXPRESSION_LOGIC_OPERATORS.LE if upper_eq else CONST_EXPRESSION_LOGIC_OPERATORS.LT

        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.AND, [
            BooleanColumnExpressionNode(lower_operator, column, lower),
            BooleanColumnExpressionNode(upper_operator, column, upper)
        ])


    @classmethod
    def in_list(cls, column: str, values: List[Any]) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IN, column, values)


    @classmethod
    def is_null(cls, column: str) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL, column)

    @classmethod
    def not_null(cls, column: str) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL, column)

    # =====================================
    # Column to Column comparison
    # =====================================
    @classmethod
    def column_equals(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.EQ, column1, None, compare_column=column2)

    @classmethod
    def column_not_equals(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NE, column1, None, compare_column=column2)

    @classmethod
    def column_greater_than(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GT, column1, None, compare_column=column2)

    @classmethod
    def column_less_than(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LT, column1, None, compare_column=column2)

    @classmethod
    def column_greater_than_or_equal(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GE, column1, None, compare_column=column2)

    @classmethod
    def column_less_than_or_equal(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return BooleanColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LE, column1, None, compare_column=column2)


    # =====================================
    # Shortcut Aliases - Values
    # =====================================
    @classmethod
    def eq(cls, column: str, value: Any) -> BooleanColumnExpressionNode:
        return cls.equals(column, value)

    @classmethod
    def ne(cls, column: str, value: Any) -> BooleanColumnExpressionNode:
        return cls.not_equals(column, value)

    @classmethod
    def gt(cls, column: str, value: Any) -> BooleanColumnExpressionNode:
        return cls.greater_than(column, value)

    @classmethod
    def lt(cls, column: str, value: Any) -> BooleanColumnExpressionNode:
        return cls.less_than(column, value)

    @classmethod
    def ge(cls, column: str, value: Any) -> BooleanColumnExpressionNode:
        return cls.greater_than_or_equal(column, value)

    @classmethod
    def le(cls, column: str, value: Any) -> BooleanColumnExpressionNode:
        return cls.less_than_or_equal(column, value)

    # =====================================
    # Shortcut Aliases - Column to Column
    # =====================================
    @classmethod
    def col_eq(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return cls.column_equals(column1, column2)

    @classmethod
    def col_ne(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return cls.column_not_equals(column1, column2)

    @classmethod
    def col_gt(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return cls.column_greater_than(column1, column2)

    @classmethod
    def col_lt(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return cls.column_less_than(column1, column2)

    @classmethod
    def col_ge(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return cls.column_greater_than_or_equal(column1, column2)

    @classmethod
    def col_le(cls, column1: str, column2: str) -> BooleanColumnExpressionNode:
        return cls.column_less_than_or_equal(column1, column2)





    # =====================================
    # Literal Comparisons
    # =====================================
    @classmethod
    def literal_is_null(cls, value1: Any) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL, value1)

    @classmethod
    def literal_not_null(cls, value1: Any) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL, value1)

    # =====================================
    # Column to Column comparison
    # =====================================
    @classmethod
    def literal_equals(cls, value1: Any, value2: Any) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.EQ, value1, value2)

    @classmethod
    def literal_not_equals(cls, value1: Any, value2: Any) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NE, value1, value2)

    @classmethod
    def literal_greater_than(cls, value1: Any, value2: Any) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GT, value1, value2)

    @classmethod
    def literal_less_than(cls, value1: Any, value2: Any) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LT, value1, value2)

    @classmethod
    def literal_greater_than_or_equal(cls, value1: Any, value2: Any) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GE, value1, value2)

    @classmethod
    def literal_less_than_or_equal(cls, value1: Any, value2: Any) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LE, value1, value2)


    @classmethod
    def literal_between(cls, value1: str, lower: Union[int, float], upper: Union[int, float], lower_eq: bool=True, upper_eq: bool = True) -> BooleanLogicalExpressionNode:

        lower_operator = CONST_EXPRESSION_LOGIC_OPERATORS.GE if lower_eq else CONST_EXPRESSION_LOGIC_OPERATORS.GT
        upper_operator = CONST_EXPRESSION_LOGIC_OPERATORS.LE if upper_eq else CONST_EXPRESSION_LOGIC_OPERATORS.LT

        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.AND, [
            BooleanLiteralExpressionNode(lower_operator, value1, lower),
            BooleanLiteralExpressionNode(upper_operator, value1, upper)
        ])


    @classmethod
    def literal_in_list(cls, value1: Any, values: List[Any]) -> BooleanLiteralExpressionNode:
        return BooleanLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IN, value1, values)


    # =====================================
    # Logical operators on a single BooleanColumnExpressionNodes
    # =====================================
    @classmethod
    def not_(cls, expression: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        """Unary Operator - only negates a single expresion"""
        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NOT, [expression])

    # =====================================
    # Logical operators on multiple BooleanColumnExpressionNodes
    # =====================================
    @classmethod
    def and_(cls, *expressions: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.AND, list(expressions))

    @classmethod
    def or_(cls, *expressions: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.OR, list(expressions))


    @classmethod
    def xor_(cls, *expressions: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        """Exclusive OR: exactly one expressions must be TRUE."""
        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.XOR_EXCLUSIVE, list(expressions))

    @classmethod
    def xor_parity(cls, *expressions: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        """Parity XOR: odd number of expressions must be TRUE."""
        return BooleanLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.XOR_PARITY, list(expressions))



    @classmethod
    def all(cls, *expressions: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        """Equivalent to AND(condition1, condition2, ...)"""
        return cls.and_(*expressions)

    @classmethod
    def any(cls, *expressions: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        """Equivalent to OR(condition1, condition2, ...)"""
        combined = cls.or_(*expressions)
        return cls.or_(*expressions)

    @classmethod
    def not_all(cls, *expressions: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        """NOT(condition1 AND condition2 AND ...) - De Morgan's law"""
        combined = cls.and_(*expressions)
        return cls.not_(combined)

    @classmethod
    def not_any(cls, *expressions: BooleanExpressionNode) -> BooleanLogicalExpressionNode:
        """NOT(condition1 OR condition2 OR ...) - De Morgan's law"""
        combined = cls.or_(*expressions)
        return cls.not_(combined)
