from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional

from ibis.expr.types import s

from ...constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_EXPRESSION_NODE_TYPES
from ...visitors.core.base_visitor import Visitor


class ExpressionNode(ABC):

    @property
    @abstractmethod
    def _expression_type(self) -> str:
        pass

    @property
    def expression_type(self) -> str:
        return self._expression_type


    @property
    @abstractmethod
    def _logic_type(self) -> str:
        pass

    @property
    def logic_type(self) -> str:
        return self._logic_type


    @abstractmethod
    def accept(self, visitor: 'Visitor') -> Callable:
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


    def __init__(self, operator: str, value1: Any, value2: Any):

        self.operator = operator
        self.value1 = value1
        self.value2 = value2

    @property
    def _expression_type(self) -> str:
        return CONST_EXPRESSION_NODE_TYPES.LITERAL


    @abstractmethod
    def accept(self, visitor: 'Visitor') -> Callable:
        pass

class ColumnExpressionNode(ExpressionNode):

    def __init__(self, operator: str, column: str, value: Optional[Any], compare_column: Optional[str] = None):
        self.operator = operator
        self.column = column
        self.value = value
        self.compare_column = compare_column

    @property
    def _expression_type(self) -> str:
        return CONST_EXPRESSION_NODE_TYPES.COLUMN


    @abstractmethod
    def accept(self, visitor: 'Visitor') -> Callable:
        pass

class LogicalExpressionNode(ExpressionNode):

    @property
    def _expression_type(self) -> str:
        return CONST_EXPRESSION_NODE_TYPES.LOGICAL


    def __init__(self, operator: str, operands: List[ExpressionNode]):
        self.operator = operator
        self.operands = operands
