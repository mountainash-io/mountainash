
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod

from ...constants import CONST_EXPRESSION_CAST_OPERATORS

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode, CastExpressionNode
    from ...expression_parameters import ExpressionParameter

class CastExpressionVisitor(ABC):

    @property
    def cast_ops(self) -> Dict[str, Callable]:
        cast_ops = {
            CONST_EXPRESSION_CAST_OPERATORS.CAST:   self._cast,
        }

        return cast_ops



    def visit_cast_expression(self, expression_node: CastExpressionNode) -> Any:

        if expression_node.operator not in self.cast_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        type_parameter =  ExpressionParameter(expression_node.type)
        type_expression_node = type_parameter.resolve_to_expression_node()

        return self._process_cast_expression(expression_node, type_expression_node)


    def _process_cast_expression(self, expression_node: CastExpressionNode, value_expression_node: "ExpressionNode") -> Any:

        if expression_node.operator not in self.cast_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.cast_ops[expression_node.operator]
        return op_func(value_expression_node, expression_node.type, **expression_node.kwargs)


    @abstractmethod
    def _cast(self, value: Any, type: Any, **kwargs) -> Any:
        pass
