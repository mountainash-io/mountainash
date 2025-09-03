
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod

from ..constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS

if TYPE_CHECKING:
    from .expression_nodes import ExpressionNode


class ExpressionVisitor(ABC):

    @property
    @abstractmethod
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        pass

    @property
    @abstractmethod
    def logic_type(self) -> CONST_LOGIC_TYPES:
        pass


    @property
    def source_ops(self) -> Dict[str, Callable]:
        source_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.COL:   self._col,
        }

        return source_ops

    @property
    def literal_ops(self) -> Dict[str, Callable]:
        literal_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.LIT:   self._lit,
        }

        return literal_ops

    @property
    def cast_ops(self) -> Dict[str, Callable]:
        cast_ops = {
            CONST_EXPRESSION_LOGIC_OPERATORS.CAST:   self._cast,
        }

        return cast_ops


    @abstractmethod
    def _col(self,  value: str) -> Any:
        pass

    @abstractmethod
    def _lit(self, value: Any) -> Any:
        pass


    @abstractmethod
    def _cast(self, value: Any, type: Any, **kwargs) -> Any:
        pass




    # @abstractmethod
    # def visit_logical_expression(self, expression_node: "ExpressionNode") -> Callable:
    #     pass

    # @abstractmethod
    # def visit_comparison_expression(self, expression_node: "ExpressionNode") -> Callable:
    #     pass

    # @abstractmethod
    # def visit_conditional_expression(self, expression_node: "ExpressionNode") -> Callable:
    #     pass

    # @abstractmethod
    # def visit_arithmetic_expression(self, expression_node: "ExpressionNode") -> Callable:
    #     pass
