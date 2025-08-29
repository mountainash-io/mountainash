
from typing import Callable
from abc import ABC, abstractmethod
from ...logic.core import LiteralExpressionNode, ColumnExpressionNode, LogicalExpressionNode
from .base_visitor import Visitor

class ExpressionVisitor(Visitor):

    @property
    @abstractmethod
    def _logic_type(self) -> str:
        pass

    @property
    def logic_type(self) -> str:
        return self._logic_type


    @abstractmethod
    def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:
        pass

    @abstractmethod
    def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:
        pass

    @abstractmethod
    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:
        pass
