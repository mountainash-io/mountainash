
from typing import Callable, TYPE_CHECKING
from abc import ABC, abstractmethod

from ..constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS

if TYPE_CHECKING:
    from ..logic.expression_node_protocol import ExpressionNodeProtocol


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
    def visit_literal_expression(self, expression_node: "ExpressionNodeProtocol") -> Callable:
        pass

    @abstractmethod
    def visit_column_expression(self, expression_node: "ExpressionNodeProtocol") -> Callable:
        pass

    @abstractmethod
    def visit_logical_expression(self, expression_node: "ExpressionNodeProtocol") -> Callable:
        pass
