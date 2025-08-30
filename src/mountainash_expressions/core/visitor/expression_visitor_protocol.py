
from typing import Callable, Protocol

from ..logic import LiteralExpressionNode, ColumnExpressionNode, LogicalExpressionNode
from ..constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS


class ExpressionVisitorProtocol(Protocol):
    """Protocol for expression nodes"""
    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS: ...

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES: ...


    def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable: ...

    def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable: ...

    def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable: ...
