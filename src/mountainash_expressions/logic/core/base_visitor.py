# from typing import Any, List, Union, Callable, Optional
# from abc import ABC, abstractmethod
# from .base_nodes import ExpressionNode, ColumnExpressionNode, LogicalExpressionNode, LiteralExpressionNode


# class ExpressionVisitor(ABC):

#     # @abstractmethod
#     # def visit_raw_expression(self, expression_node: RawExpressionNode) -> Callable:
#     #     pass

#     @abstractmethod
#     def visit_literal_expression(self, expression_node: LiteralExpressionNode) -> Callable:
#         pass

#     @abstractmethod
#     def visit_column_expression(self, expression_node: ColumnExpressionNode) -> Callable:
#         pass

#     @abstractmethod
#     def visit_logical_expression(self, expression_node: LogicalExpressionNode) -> Callable:
#         pass



#     # @property
#     # def arithmetic_ops(self) -> Dict:
#     #     """Dynamic property to get arithmetic operations."""
#     #     return self._boolean_comparison_ops()

#     # @abstractmethod
#     # def _arithmetic_ops(self) -> Dict:
#     #     """Abstract method to define arithmetic operations."""
#     #     pass
