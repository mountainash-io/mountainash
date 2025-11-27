
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod

from ...constants import CONST_EXPRESSION_LITERAL_OPERATORS
from ...expression_parameters import ExpressionParameter

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode, LiteralExpressionNode

class LiteralExpressionVisitor(ABC):

    @property
    def literal_ops(self) -> Dict[str, Callable]:
        literal_ops = {
            CONST_EXPRESSION_LITERAL_OPERATORS.LIT:   self._lit,
        }

        return literal_ops



    def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Any:

        if expression_node.operator not in self.literal_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        value_parameter =  ExpressionParameter(expression_node.value)
        value_expression_node = value_parameter.resolve_to_expression_node()

        return self._process_literal_expression(expression_node, value_expression_node)


    def _process_literal_expression(self, expression_node: LiteralExpressionNode, value_expression_node: "ExpressionNode") -> Any:

        if expression_node.operator not in self.literal_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.literal_ops[expression_node.operator]
        return op_func(value_expression_node)


    @abstractmethod
    def _lit(self, value: Any) -> Any:
        pass
