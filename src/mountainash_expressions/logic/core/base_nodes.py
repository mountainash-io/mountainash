from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional

from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS


class ExpressionNode(ABC):
    @abstractmethod
    def accept(self, visitor: 'ExpressionVisitor') -> Callable:
        pass

    @abstractmethod
    def eval(self) -> Callable:
        pass

    @abstractmethod
    def eval_is_true(self) -> Callable:
        """Convert result to boolean TRUE check."""
        pass

    @abstractmethod
    def eval_is_false(self) -> Callable:
        """Convert result to boolean FALSE check."""
        pass



class LiteralExpressionNode(ExpressionNode):

    expression_type = "literal"

    def __init__(self, operator: str, value1: Any, value2: Any):
        self.operator = operator
        self.value1 = value1
        self.value2 = value2

    @abstractmethod
    def accept(self, visitor: 'ExpressionVisitor') -> Callable:
        pass

class ColumnExpressionNode(ExpressionNode):

    expression_type = "column"

    def __init__(self, operator: str, column: str, value: Optional[Any], compare_column: Optional[str] = None):
        self.operator = operator
        self.column = column
        self.value = value
        self.compare_column = compare_column

    @abstractmethod
    def accept(self, visitor: 'ExpressionVisitor') -> Callable:
        pass

class LogicalExpressionNode(ExpressionNode):

    expression_type = "logical"

    def __init__(self, operator: str, operands: List[ExpressionNode]):
        self.operator = operator
        self.operands = operands


class ExpressionVisitor(ABC):

    @abstractmethod
    def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:
        pass

    @abstractmethod
    def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:
        pass

    @abstractmethod
    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:
        pass
