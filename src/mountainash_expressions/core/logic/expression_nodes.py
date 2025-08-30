from abc import ABC, abstractmethod
from typing import Any, List, Union, Callable, Optional, Protocol, final

from ibis.expr.types import s

from ..constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES
from ..visitor import ExpressionVisitorProtocol


class ExpressionNodeProtocol(Protocol):
    """Protocol for expression nodes"""
    @property
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES: ...

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES: ...



class ExpressionNode(ABC):


    @property
    @abstractmethod
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        pass

    @property
    @abstractmethod
    def logic_type(self) -> CONST_LOGIC_TYPES:
        pass


    @abstractmethod
    def accept(self, visitor: ExpressionVisitorProtocol) -> Callable:
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
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.LITERAL


    @abstractmethod
    def accept(self, visitor: ExpressionVisitorProtocol) -> Callable:
        pass

class ColumnExpressionNode(ExpressionNode):

    def __init__(self, operator: str, column: str, value: Optional[Any], compare_column: Optional[str] = None):
        self.operator = operator
        self.column = column
        self.value = value
        self.compare_column = compare_column

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.COLUMN


    @abstractmethod
    def accept(self, visitor: ExpressionVisitorProtocol) -> Callable:
        pass

class LogicalExpressionNode(ExpressionNode):

    @property
    @final
    def expression_type(self) -> CONST_EXPRESSION_NODE_TYPES:
        return CONST_EXPRESSION_NODE_TYPES.LOGICAL


    def __init__(self, operator: str, operands: List[ExpressionNode]):
        self.operator = operator
        self.operands = operands
