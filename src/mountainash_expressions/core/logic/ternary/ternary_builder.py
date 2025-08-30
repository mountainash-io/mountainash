# file: src/mountainash_dataframes/utils/expressions/ternary/base.py



from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional
from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS

from .ternary_nodes import TernaryExpressionNode, TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryLiteralExpressionNode

class TernaryExpressionBuilder:

    #############
    # Shortcut Aliases - Values
    @classmethod
    def eq(cls, column: str, value: Any) -> TernaryColumnExpressionNode:
        return cls.equals(column, value)

    @classmethod
    def ne(cls, column: str, value: Any) -> TernaryColumnExpressionNode:
        return cls.not_equals(column, value)

    @classmethod
    def gt(cls, column: str, value: Any) -> TernaryColumnExpressionNode:
        return cls.greater_than(column, value)

    @classmethod
    def lt(cls, column: str, value: Any) -> TernaryColumnExpressionNode:
        return cls.less_than(column, value)

    @classmethod
    def ge(cls, column: str, value: Any) -> TernaryColumnExpressionNode:
        return cls.greater_than_or_equal(column, value)

    @classmethod
    def le(cls, column: str, value: Any) -> TernaryColumnExpressionNode:
        return cls.less_than_or_equal(column, value)

    #############
    # Shortcut Aliases - Column to Column
    @classmethod
    def col_eq(cls, column_lhs: str, column_rhs: str) -> TernaryColumnExpressionNode:
        return cls.column_equals(column_lhs, column_rhs)

    @classmethod
    def col_ne(cls, column_lhs: str, column_rhs: str) -> TernaryColumnExpressionNode:
        return cls.column_not_equals(column_lhs, column_rhs)

    @classmethod
    def col_gt(cls, column_lhs: str, column_rhs: str) -> TernaryColumnExpressionNode:
        return cls.column_greater_than(column_lhs, column_rhs)

    @classmethod
    def col_lt(cls, column_lhs: str, column_rhs: str) -> TernaryColumnExpressionNode:
        return cls.column_less_than(column_lhs, column_rhs)

    @classmethod
    def col_ge(cls, column_lhs: str, column_rhs: str) -> TernaryColumnExpressionNode:
        return cls.column_greater_than_or_equal(column_lhs, column_rhs)

    @classmethod
    def col_le(cls, column_lhs: str, column_rhs: str) -> TernaryColumnExpressionNode:
        return cls.column_less_than_or_equal(column_lhs, column_rhs)



    #####  Actual Implementations ####

    @classmethod
    def always_true(cls) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_TRUE, [])

    @classmethod
    def always_false(cls) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_FALSE, [])

    @classmethod
    def always_unknown(cls) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_UNKNOWN, [])


    # Column to Value comparison
    @classmethod
    def equals(cls, column_lhs: str, value: Any) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.EQ, column_lhs, value)

    @classmethod
    def not_equals(cls, column_lhs: str, value: Any) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NE, column_lhs, value)

    @classmethod
    def greater_than(cls, column_lhs: str, value: Union[int, float]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GT, column_lhs, value)

    @classmethod
    def less_than(cls, column_lhs: str, value: Union[int, float]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LT, column_lhs, value)

    @classmethod
    def greater_than_or_equal(cls, column_lhs: str, value: Union[int, float]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GE, column_lhs, value)

    @classmethod
    def less_than_or_equal(cls, column_lhs: str, value: Union[int, float]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LE, column_lhs, value)


    @classmethod
    def between(cls, column_lhs: str, lower: Union[int, float], upper: Union[int, float], lower_eq: bool=True, upper_eq: bool = True) -> TernaryLogicalExpressionNode:

        lower_operator = CONST_EXPRESSION_LOGIC_OPERATORS.GE if lower_eq else CONST_EXPRESSION_LOGIC_OPERATORS.GT
        upper_operator = CONST_EXPRESSION_LOGIC_OPERATORS.LE if upper_eq else CONST_EXPRESSION_LOGIC_OPERATORS.LT

        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.AND, [
            TernaryColumnExpressionNode(lower_operator, column_lhs, lower),
            TernaryColumnExpressionNode(upper_operator, column_lhs, upper)
        ])

    @classmethod
    def in_list(cls, column: str, values: List[Any]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IN, column, values)


    @classmethod
    def is_null(cls, column: str) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL, column, None)

    @classmethod
    def not_null(cls, column: str) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL, column, None)

    # Column to Column comparison
    @classmethod
    def column_equals(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.EQ, column1, None, compare_column=column2)

    @classmethod
    def column_not_equals(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NE, column1, None, compare_column=column2)

    @classmethod
    def column_greater_than(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GT, column1, None, compare_column=column2)

    @classmethod
    def column_less_than(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LT, column1, None, compare_column=column2)

    @classmethod
    def column_greater_than_or_equal(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GE, column1, None, compare_column=column2)

    @classmethod
    def column_less_than_or_equal(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LE, column1, None, compare_column=column2)




    # =====================================
    # Literal Comparisons
    # =====================================
    @classmethod
    def literal_is_null(cls, value: Any) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_NULL, value, None)

    @classmethod
    def literal_not_null(cls, value: Any) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_NOT_NULL, value, None)

    # =====================================
    # Column to Column comparison
    # =====================================
    @classmethod
    def literal_equals(cls, value_lhs: Any, value2: Any) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.EQ, value_lhs, value2)

    @classmethod
    def literal_not_equals(cls, value_lhs: Any, value2: Any) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NE, value_lhs, value2)

    @classmethod
    def literal_greater_than(cls, value_lhs: Any, value2: Any) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GT, value_lhs, value2)

    @classmethod
    def literal_less_than(cls, value_lhs: Any, value2: Any) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LT, value_lhs, value2)

    @classmethod
    def literal_greater_than_or_equal(cls, value_lhs: Any, value2: Any) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GE, value_lhs, value2)

    @classmethod
    def literal_less_than_or_equal(cls, value_lhs: Any, value2: Any) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LE, value_lhs, value2)


    @classmethod
    def literal_between(cls, value_lhs: str, lower: Union[int, float], upper: Union[int, float], lower_eq: bool=True, upper_eq: bool = True) -> TernaryLogicalExpressionNode:

        lower_operator = CONST_EXPRESSION_LOGIC_OPERATORS.GE if lower_eq else CONST_EXPRESSION_LOGIC_OPERATORS.GT
        upper_operator = CONST_EXPRESSION_LOGIC_OPERATORS.LE if upper_eq else CONST_EXPRESSION_LOGIC_OPERATORS.LT

        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.AND, [
            TernaryLiteralExpressionNode(lower_operator, value_lhs, lower),
            TernaryLiteralExpressionNode(upper_operator, value_lhs, upper)
        ])


    @classmethod
    def literal_in_list(cls, value_lhs: Any, values: List[Any]) -> TernaryLiteralExpressionNode:
        return TernaryLiteralExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IN, value_lhs, values)



    # N-ary Logical operators on multiple ColumnConditions

    @classmethod
    def and_(cls, *conditions: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.AND, list(conditions))


    @classmethod
    def or_(cls, *conditions: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.OR, list(conditions))

    @classmethod
    def xor_(cls, *conditions: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        """Exclusive OR: TRUE if exactly ONE condition is TRUE.

        With multiple operands, XOR returns TRUE only when exactly one
        operand is TRUE and all others are FALSE. If any operand is UNKNOWN,
        the result may be UNKNOWN depending on the other values.
        """
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.XOR_EXCLUSIVE, list(conditions))



    #Unary logical operations
    @classmethod
    def is_true(cls, condition: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_TRUE, [condition])

    @classmethod
    def is_false(cls, condition: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_FALSE, [condition])

    @classmethod
    def is_unknown(cls, condition: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_UNKNOWN, [condition])

    @classmethod
    def maybe_true(cls, condition: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.MAYBE_TRUE, [condition])

    @classmethod
    def maybe_false(cls, condition: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.MAYBE_FALSE, [condition])

    @classmethod
    def is_known(cls, condition: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.IS_KNOWN, [condition])


    @classmethod
    def not_(cls, condition: TernaryExpressionNode) -> TernaryLogicalExpressionNode:
        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NOT, [condition])
