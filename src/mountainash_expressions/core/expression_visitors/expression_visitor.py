
from typing import Callable, TYPE_CHECKING, Dict, Any
from abc import ABC, abstractmethod
from enum import Enum

from ..constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS
# from ..expression_nodes import (
#     SourceExpressionNode,
#     LiteralExpressionNode,
#     CastExpressionNode,
#     LogicalConstantExpressionNode,
#     UnaryExpressionNode,
# )
from ..expression_parameters import ExpressionParameter
from ..expression_system.base import ExpressionSystem
from ..protocols.core.column import ENUM_COLUMN_OPERATORS, ColumnVisitorProtocol, ColumnOperatorProtocol
from ..protocols.core.literal import ENUM_LITERAL_OPERATORS, LiteralVisitorProtocol, LiteralOperatorProtocol

from ...types import SupportedExpressions

if TYPE_CHECKING:
    from ..expression_nodes import (

    ExpressionNode,
    ColumnExpressionNode,
    LiteralExpressionNode,
    # NativeBackendExpressionNode,
    # CastExpressionNode,
    # LogicalConstantExpressionNode,
    # UnaryExpressionNode,
    # LogicalExpressionNode,
    # ComparisonExpressionNode,
    # CollectionExpressionNode,
    # ArithmeticExpressionNode,
    # ConditionalIfElseExpressionNode,
)



class ExpressionVisitor() #ColumnVisitorProtocol, LiteralVisitorProtocol):

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

    # @abstractmethod
    # def visit_literal_expression(self, node: LiteralExpressionNode) -> SupportedExpressions: ...


    # @property
    # def source_ops(self) -> Dict[str, Callable]:
    #     source_ops = {
    #         CONST_EXPRESSION_LOGIC_OPERATORS.COL:   self._col,
    #     }

    #     return source_ops

    # @property
    # def literal_ops(self) -> Dict[str, Callable]:
    #     literal_ops = {
    #         CONST_EXPRESSION_LOGIC_OPERATORS.LIT:   self._lit,
    #     }

    #     return literal_ops

    # @property
    # def cast_ops(self) -> Dict[str, Callable]:
    #     cast_ops = {
    #         CONST_EXPRESSION_LOGIC_OPERATORS.CAST:   self._cast,
    #     }

    #     return cast_ops


    # def visit_source_expression(self, expression_node: SourceExpressionNode) -> Any:

    #     if expression_node.operator not in self.source_ops:
    #         raise ValueError(f"Unsupported operator: {expression_node.operator}")

    #     value_parameter =  ExpressionParameter(expression_node.operand)
    #     value_expression_node = value_parameter.resolve_to_expression_node()

    #     return self._process_source_expression(expression_node, value_expression_node)


    # def _process_source_expression(self, expression_node: SourceExpressionNode, value_expression_node: "ExpressionNode") -> Any:

    #     if expression_node.operator not in self.source_ops:
    #         raise ValueError(f"Unsupported operator: {expression_node.operator}")

    #     op_func = self.source_ops[expression_node.operator]
    #     return op_func(value_expression_node)


    # def visit_literal_expression(self, expression_node: SourceExpressionNode) -> Any:

    #     if expression_node.operator not in self.literal_ops:
    #         raise ValueError(f"Unsupported operator: {expression_node.operator}")

    #     value_parameter =  ExpressionParameter(expression_node.operand)
    #     value_expression_node = value_parameter.resolve_to_expression_node()

    #     return self._process_literal_expression(expression_node, value_expression_node)


    # def _process_literal_expression(self, expression_node: LiteralExpressionNode, value_expression_node: "ExpressionNode") -> Any:

    #     if expression_node.operator not in self.literal_ops:
    #         raise ValueError(f"Unsupported operator: {expression_node.operator}")

    #     op_func = self.literal_ops[expression_node.operator]
    #     return op_func(value_expression_node)


    # def visit_cast_expression(self, expression_node: CastExpressionNode) -> Any:

    #     if expression_node.operator not in self.cast_ops:
    #         raise ValueError(f"Unsupported operator: {expression_node.operator}")

    #     value_parameter =  ExpressionParameter(expression_node.operand)
    #     value_expression_node = value_parameter.resolve_to_expression_node()

    #     return self._process_cast_expression(expression_node, value_expression_node)


    # def _process_cast_expression(self, expression_node: CastExpressionNode, value_expression_node: "ExpressionNode") -> Any:

    #     if expression_node.operator not in self.cast_ops:
    #         raise ValueError(f"Unsupported operator: {expression_node.operator}")

    #     op_func = self.cast_ops[expression_node.operator]
    #     return op_func(value_expression_node, expression_node.type, **expression_node.kwargs)





    # @abstractmethod
    # def _col(self,  value: str) -> Any:
    #     pass

    # @abstractmethod
    # def _lit(self, value: Any) -> Any:
    #     pass


    # @abstractmethod
    # def _cast(self, value: Any, type: Any, **kwargs) -> Any:
    #     pass






    # @abstractmethod
    # def visit_cast_expression(self, expression_node: CastExpressionNode) -> Callable:
    #     pass

    # # @abstractmethod
    # # def visit_native_expression(self, expression_node: "NativeBackendExpressionNode") -> Callable:
    # #     pass


    # @abstractmethod
    # def visit_unary_expression(self, expression_node: UnaryExpressionNode) -> Callable:
    #     pass

    # @abstractmethod
    # def visit_logical_constant_expression(self, expression_node: LogicalConstantExpressionNode) -> Callable:
    #     pass


    # @abstractmethod
    # def visit_logical_expression(self, expression_node: "LogicalExpressionNode") -> Callable:
    #     pass

    # @abstractmethod
    # def visit_comparison_expression(self, expression_node: "ComparisonExpressionNode") -> Callable:
    #     pass

    # @abstractmethod
    # def visit_collection_expression(self, expression_node: "CollectionExpressionNode") -> Callable:
    #     pass


    # @abstractmethod
    # def visit_conditional_expression(self, expression_node: ConditionalExpressionNode) -> Callable:
    #     pass

    # @abstractmethod
    # def visit_arithmetic_expression(self, expression_node: ArithmeticExpressionNode) -> Callable:
    #     pass
