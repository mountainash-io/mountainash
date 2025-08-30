
from typing import Callable, Protocol
from abc import ABC, abstractmethod

from ..logic import LiteralExpressionNode, ColumnExpressionNode, LogicalExpressionNode
from ..constants import CONST_EXPRESSION_LOGIC_OPERATORS, CONST_EXPRESSION_NODE_TYPES, CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS
from .expression_visitor_protocol import ExpressionVisitorProtocol





class ExpressionVisitor(ABC):

    @property
    @abstractmethod
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        pass

    @property
    @abstractmethod
    def logic_type(self) -> CONST_LOGIC_TYPES:
        pass

    @abstractmethod
    def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:
        pass

    @abstractmethod
    def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:
        pass

    @abstractmethod
    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:
        pass
