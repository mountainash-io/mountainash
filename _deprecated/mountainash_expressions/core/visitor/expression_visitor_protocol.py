
from typing import Callable, Protocol, TYPE_CHECKING
from ..constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS
from abc import abstractmethod

if TYPE_CHECKING:
    from ..logic.expression_node_protocol import ExpressionNodeProtocol

class ExpressionVisitorProtocol(Protocol):
    """Protocol for expression nodes"""
    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS: ...

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES: ...



    @abstractmethod
    def visit_literal_expression(self, expression_node: "ExpressionNodeProtocol") -> Callable:
        pass

    @abstractmethod
    def visit_column_expression(self, expression_node: "ExpressionNodeProtocol") -> Callable:
        pass

    @abstractmethod
    def visit_logical_expression(self, expression_node: "ExpressionNodeProtocol") -> Callable:
        pass
