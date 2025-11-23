# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, List, Callable, Dict, TYPE_CHECKING
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto
# from ....types import SupportedExpressions

# from ...constants import CONST_EXPRESSION_LOGICAL_UNARY_OPERATORS, CONST_EXPRESSION_SOURCE_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, BooleanUnaryExpressionNode
# from ...expression_builders.base_expression_builder import ExpressionBuilder

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions


# class ENUM_BOOLEAN_UNARY_OPERATORS(Enum):
#     """
#     Enumeration for expression logical unary operators.
#     """
#     IS_TRUE = auto()
#     IS_FALSE = auto()
#     NOT = auto()

# class BooleanUnaryVisitorProtocol(Protocol):

#     @property
#     def logic_type(self) -> CONST_LOGIC_TYPES: ...

#     def visit_boolean_unary_expression(self,    node: BooleanUnaryExpressionNode) -> SupportedExpressions: ...

#     def is_true(self,   node: BooleanUnaryExpressionNode) -> SupportedExpressions: ...
#     def is_false(self,  node: BooleanUnaryExpressionNode) -> SupportedExpressions: ...
#     def not_(self,      node: BooleanUnaryExpressionNode ) -> SupportedExpressions: ...


# class BooleanUnaryExpressionProtocol(Protocol):

#     def is_true(self, expr: SupportedExpressions) -> SupportedExpressions: ...
#     def is_false(self, expr: SupportedExpressions) -> SupportedExpressions: ...
#     def not_(self, expr: SupportedExpressions ) -> SupportedExpressions: ...


# class BooleanUnaryBuilderProtocol(Protocol):

#     def is_true(self) -> ExpressionBuilder: ...
#     def is_false(self) -> ExpressionBuilder: ...
#     def not_(self ) -> ExpressionBuilder: ...
