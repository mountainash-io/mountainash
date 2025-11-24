
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

from ...constants import  CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode
    from ..expression_system.base import ExpressionSystem
    from ...types import SupportedExpressions



class ExpressionVisitor(ABC):

    @property
    @abstractmethod
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        pass

    @property
    @abstractmethod
    def logic_type(self) -> CONST_LOGIC_TYPES:
        pass


    def __init__(self, expression_system: ExpressionSystem):
        """
        Initialize with an ExpressionSystem implementation.

        Args:
            expression_system: Backend-specific ExpressionSystem
        """
        self.backend: ExpressionSystem = expression_system


    def _get_expr_op(self, expr_ops: Dict[Enum, Callable], node: ExpressionNode) -> Callable:
        if (op_func := expr_ops.get(node.operator, None)) is None:
            raise ValueError(f"Unsupported operator: {node.operator}")

        return op_func


    @abstractmethod
    def visit_expression_node(self, node: Any) -> SupportedExpressions: ...
