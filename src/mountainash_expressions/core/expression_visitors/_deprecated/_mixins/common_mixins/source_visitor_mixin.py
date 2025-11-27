
from __future__ import annotations
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod

from ...constants import CONST_EXPRESSION_SOURCE_OPERATORS

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode, SourceExpressionNode
    from ...expression_parameters import ExpressionParameter

class SourceExpressionVisitor(ABC):

    @property
    def source_ops(self) -> Dict[str, Callable]:
        source_ops = {
            CONST_EXPRESSION_SOURCE_OPERATORS.COL:   self._col,

            CONST_EXPRESSION_SOURCE_OPERATORS.IS_NULL:       self._is_null,
            CONST_EXPRESSION_SOURCE_OPERATORS.IS_NOT_NULL:   self._is_not_null,

        }

        return source_ops



    @abstractmethod
    def _col(self,  column: Any, /,  **kwargs) -> Any:
        pass

    @abstractmethod
    def _is_null(self, LHS: ExpressionNode) -> Any:
        pass

    @abstractmethod
    def _is_not_null(self, LHS: ExpressionNode) -> Any:
        pass



    def visit_source_expression(self, expression_node: SourceExpressionNode) -> Any:

        if expression_node.operator not in self.source_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        value_parameter =  ExpressionParameter(expression_node.value)
        value_expression_node = value_parameter.resolve_to_expression_node()

        return self._process_source_expression(expression_node, value_expression_node)


    def _process_source_expression(self, expression_node: SourceExpressionNode, value_expression_node: "ExpressionNode") -> Any:

        if expression_node.operator not in self.source_ops:
            raise ValueError(f"Unsupported operator: {expression_node.operator}")

        op_func = self.source_ops[expression_node.operator]
        return op_func(value_expression_node)
