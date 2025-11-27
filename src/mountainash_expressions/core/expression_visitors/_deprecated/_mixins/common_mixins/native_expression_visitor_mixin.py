
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod

from ...constants import CONST_EXPRESSION_NATIVE_OPERATORS

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode, NativeBackendExpressionNode
    from ...expression_parameters import ExpressionParameter

class NativeBackendExpressionVisitor(ABC):

    @property
    def native_expresssion_ops(self) -> Dict[str, Callable]:
        source_ops = {
            CONST_EXPRESSION_NATIVE_OPERATORS.NATIVE:   self._native_expression,
        }

        return native_expresssion_ops




    def visit_native_expression(self, expression_node: NativeBackendExpressionNode) -> Any:

        if expression_node.operator not in self.native_expresssion_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        value_parameter =  ExpressionParameter(expression_node.operand)
        value_expression_node = value_parameter.resolve_to_expression_node()

        return self._process_native_expression(expression_node, value_expression_node)


    def _process_native_expression(self, expression_node: NativeBackendExpressionNode) -> Any:

        if expression_node.operator not in self.native_expresssion_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.native_expresssion_ops[expression_node.operator]
        return op_func(value_expression_node)




    @abstractmethod
    def _native_expression(self,  expr: ExpressionNode) -> Any:
        """Process native expression node."""
        pass
