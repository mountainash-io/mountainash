# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, List, Callable, Dict, TYPE_CHECKING, Union
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto
# from ....types import SupportedExpressions

# from ...constants import CONST_EXPRESSION_LOGICAL_COLLECTION_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, LogicalExpressionNode, ComparisonExpressionNode, CollectionExpressionNode, UnaryExpressionNode
# from ...expression_builders.base_expression_builder import ExpressionBuilder

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions


# class ENUM_BOOLEAN_COLLECTION_OPERATORS(Enum):
#     """
#     Enumeration for expression logical collection operators.
#     """

#     # Comparison operators
#     IS_IN =  auto()
#     IS_NOT_IN =  auto()

# class BooleanCollectionVisitorProtocol(Protocol):

#     @property
#     def logic_type(self) -> CONST_LOGIC_TYPES: ...

#     def visit_boolean_collection_expression(self, node: CollectionExpressionNode) -> SupportedExpressions: ...

#     def is_in(self,     node: CollectionExpressionNode) -> SupportedExpressions: ...
#     def is_not_in(self, node: CollectionExpressionNode) -> SupportedExpressions: ...


# class BooleanCollectionExpressionProtocol(Protocol):

#     def is_in(self,     left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def is_not_in(self, left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...


# class BooleanCollectionBuilderProtocol(Protocol):

#     def is_in(self,     other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def is_not_in(self, other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
