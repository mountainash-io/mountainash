from __future__ import annotations

from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

from ...constants import  CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode
    from ..expression_system.base import ExpressionSystem
    from ...types import SupportedExpressions



class ExpressionVisitor(ABC):
    """
    Base class for expression visitors.

    Visitors are backend-agnostic and work with any backend through
    the injected ExpressionSystem. Backend type can be determined via
    self.backend.backend_type if needed.
    """

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
