# file: src/mountainash_dataframes/utils/expressions/ternary/base.py



from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional
from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS

from .ternary_nodes import TernaryExpressionNode, TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryLiteralExpressionNode


# class TernaryExpressionNode(ABC):
#     @abstractmethod
#     def accept(self, visitor: 'TernaryExpressionVisitor') -> Callable:
#         pass

#     # #TODO: We need a VisitorFactory, based upon the type of visitor we want to use.
#     # # This is a placeholder for the visitor type, which should be defined based on the context
#     # def expr(self, vistor_type: str, mode: str) -> Callable:

#     #     visitor = TernaryVisitorFactory.get_visitor(vistor_type, mode)
#     #     return self.accept(visitor)


# class TernaryLiteralExpressionNode(TernaryExpressionNode):

#     def __init__(self, value1: Any, operator: str, value2: Any):
#         self.value1 = value1
#         self.operator = operator
#         self.value2 = value2

#     def accept(self, visitor: 'TernaryExpressionVisitor') -> Callable:
#         return visitor.visit_ternary_literal_expression(self)


# class TernaryColumnExpressionNode(TernaryExpressionNode):
#     def __init__(self, column: str, operator: str, value: Any, compare_column: Optional[str] = None):
#         self.column = column
#         self.operator = operator
#         self.value = value
#         self.compare_column = compare_column

#     def accept(self, visitor: 'TernaryExpressionVisitor') -> Callable:
#         return visitor.visit_ternary_column_expression(self)





# class TernaryLogicalExpressionNode(TernaryExpressionNode):
#     # ALWAYS_TRUE_OP = "__always_true__"
#     # ALWAYS_FALSE_OP = "__always_false__"
#     # ALWAYS_UNKNOWN_OP = "__always_unknown__"

#     def __init__(self, operator: str, operands: List[TernaryExpressionNode]):
#         self.operator = operator
#         self.operands = operands

#     @classmethod
#     def always_true(cls) -> 'TernaryLogicalExpressionNode':
#         """Creates a logical condition that always evaluates to True."""
#         return cls(operator=CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_TRUE, operands=[])

#     @classmethod
#     def always_false(cls) -> 'TernaryLogicalExpressionNode':
#         """Creates a logical condition that always evaluates to False."""
#         return cls(operator=CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_FALSE, operands=[])

#     @classmethod
#     def always_unknown(cls) -> 'TernaryLogicalExpressionNode':
#         """Creates a logical condition that always evaluates to Unknown."""
#         return cls(operator=CONST_EXPRESSION_LOGIC_OPERATORS.ALWAYS_UNKNOWN, operands=[])


#     def accept(self, visitor: 'TernaryExpressionVisitor') -> Callable:
#         return visitor.visit_ternary_logical_expression(self)

# class TernaryExpressionVisitor(ABC):

#     @abstractmethod
#     def visit_ternary_column_expression(self, expression: TernaryColumnExpressionNode) -> Callable:
#         pass

#     @abstractmethod
#     def visit_ternary_logical_expression(self, expression: TernaryLogicalExpressionNode) -> Callable:
#         pass

#     @abstractmethod
#     def visit_ternary_literal_expression(self, expression: TernaryLiteralExpressionNode) -> Callable:
#         pass


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
    def col_eq(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return cls.column_equals(column1, column2)

    @classmethod
    def col_ne(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return cls.column_not_equals(column1, column2)

    @classmethod
    def col_gt(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return cls.column_greater_than(column1, column2)

    @classmethod
    def col_lt(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return cls.column_less_than(column1, column2)

    @classmethod
    def col_ge(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return cls.column_greater_than_or_equal(column1, column2)

    @classmethod
    def col_le(cls, column1: str, column2: str) -> TernaryColumnExpressionNode:
        return cls.column_less_than_or_equal(column1, column2)



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
    def equals(cls, column: str, value: Any) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.EQ, column, value)

    @classmethod
    def not_equals(cls, column: str, value: Any) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.NE, column, value)

    @classmethod
    def greater_than(cls, column: str, value: Union[int, float]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GT, column, value)

    @classmethod
    def less_than(cls, column: str, value: Union[int, float]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LT, column, value)

    @classmethod
    def greater_than_or_equal(cls, column: str, value: Union[int, float]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.GE, column, value)

    @classmethod
    def less_than_or_equal(cls, column: str, value: Union[int, float]) -> TernaryColumnExpressionNode:
        return TernaryColumnExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.LE, column, value)


    @classmethod
    def between(cls, column: str, lower: Union[int, float], upper: Union[int, float], lower_eq: bool=True, upper_eq: bool = True) -> TernaryLogicalExpressionNode:

        lower_operator = CONST_EXPRESSION_LOGIC_OPERATORS.GE if lower_eq else CONST_EXPRESSION_LOGIC_OPERATORS.GT
        upper_operator = CONST_EXPRESSION_LOGIC_OPERATORS.LE if upper_eq else CONST_EXPRESSION_LOGIC_OPERATORS.LT

        return TernaryLogicalExpressionNode(CONST_EXPRESSION_LOGIC_OPERATORS.AND, [
            TernaryColumnExpressionNode(lower_operator, column, lower),
            TernaryColumnExpressionNode(upper_operator, column, upper)
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



    # Logical operators on multiple ColumnConditions

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
