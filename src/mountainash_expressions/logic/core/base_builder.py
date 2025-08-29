from typing import Any, List, Union
from abc import ABC, abstractmethod
from . import ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode

class ExpressionBuilder:

    #############
    # Shortcut Aliases - Values
    @classmethod
    @abstractmethod
    def eq(cls, column: str, value: Any) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def ne(cls, column: str, value: Any) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def gt(cls, column: str, value: Any) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def lt(cls, column: str, value: Any) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def ge(cls, column: str, value: Any) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def le(cls, column: str, value: Any) -> ColumnExpressionNode:
        pass


    #############
    # Shortcut Aliases - Column to Column
    @classmethod
    @abstractmethod
    def col_eq(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def col_ne(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def col_gt(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def col_lt(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def col_ge(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def col_le(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass



    #####  Actual Implementations ####

    @classmethod
    @abstractmethod
    def always_true(cls) -> LogicalExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def always_false(cls) -> LogicalExpressionNode:
        pass


    # Column to Value comparison
    @classmethod
    @abstractmethod
    def equals(cls, column: str, value: Any) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def not_equals(cls, column: str, value: Any) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def greater_than(cls, column: str, value: Union[int, float]) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def less_than(cls, column: str, value: Union[int, float]) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def greater_than_or_equal(cls, column: str, value: Union[int, float]) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def less_than_or_equal(cls, column: str, value: Union[int, float]) -> ColumnExpressionNode:
        pass


    @classmethod
    @abstractmethod
    def between(cls, column: str, lower: Union[int, float], upper: Union[int, float], lower_eq: bool=True, upper_eq: bool = True) -> LogicalExpressionNode:
        pass


    @classmethod
    @abstractmethod
    def in_list(cls, column: str, values: List[Any]) -> ColumnExpressionNode:
        pass


    @classmethod
    @abstractmethod
    def is_null(cls, column: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def not_null(cls, column: str) -> ColumnExpressionNode:
        pass

    # Column to Column comparison
    @classmethod
    @abstractmethod
    def column_equals(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def column_not_equals(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def column_greater_than(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def column_less_than(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def column_greater_than_or_equal(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def column_less_than_or_equal(cls, column1: str, column2: str) -> ColumnExpressionNode:
        pass



    #Literal Comparisons
    @classmethod
    @abstractmethod
    def literal_is_null(cls, value1: Any) -> LiteralExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def literal_not_null(cls, value1: Any) -> LiteralExpressionNode:
        pass

    # Column to Column comparison
    @classmethod
    @abstractmethod
    def literal_equals(cls, value1: Any, value2: Any) -> LiteralExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def literal_not_equals(cls, value1: Any, value2: Any) -> LiteralExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def literal_greater_than(cls, value1: Any, value2: Any) -> LiteralExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def literal_less_than(cls, value1: Any, value2: Any) -> LiteralExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def literal_greater_than_or_equal(cls, value1: Any, value2: Any) -> LiteralExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def literal_less_than_or_equal(cls, value1: Any, value2: Any) -> LiteralExpressionNode:
        pass


    @classmethod
    @abstractmethod
    def literal_between(cls, value1: str, lower: Union[int, float], upper: Union[int, float], lower_eq: bool=True, upper_eq: bool = True) -> LogicalExpressionNode:

        pass


    @classmethod
    @abstractmethod
    def literal_in_list(cls, value1: Any, values: List[Any]) -> LiteralExpressionNode:
        pass

    # Logical operators on multiple ColumnExpressionNodes
    @classmethod
    @abstractmethod
    def and_(cls, *conditions: ExpressionNode) -> LogicalExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def or_(cls, *conditions: ExpressionNode) -> LogicalExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def not_(cls, condition: ExpressionNode) -> LogicalExpressionNode:
        pass

    @classmethod
    @abstractmethod
    def xor_(cls, *conditions: ExpressionNode) -> LogicalExpressionNode:
        """Exclusive OR: exactly one condition must be TRUE."""
        pass

    @classmethod
    @abstractmethod
    def xor_parity(cls, *conditions: ExpressionNode) -> LogicalExpressionNode:
        """Parity XOR: odd number of conditions must be TRUE."""
        pass
