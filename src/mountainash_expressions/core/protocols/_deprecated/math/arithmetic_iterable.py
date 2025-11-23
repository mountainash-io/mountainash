# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, TYPE_CHECKING, Union
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_ARITHMETIC_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, ArithmeticExpressionNode
# if TYPE_CHECKING:
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_ARITHMETIC_ITERABLE_OPERATORS(Enum):
#     """
#     Enumeration for arithmetic operators.

#     Attributes:
#         - ADD: Addition (+)
#         - MULTIPLY: Multiplication (*)
#     """
#     ADD = auto()
#     MULTIPLY = auto()

# @runtime_checkable
# class ArithmeticIterableVisitorProtocol(Protocol):

#     def visit_arithmetic_iterable_expression( self, node: ArithmeticIterableExpressionNode) -> SupportedExpressions: ...

#     def add(self,       node: ArithmeticIterableExpressionNode) -> SupportedExpressions: ...
#     def multiply(self,  node: ArithmeticIterableExpressionNode) -> SupportedExpressions: ...

# @runtime_checkable
# class ArithmeticIterableExpressionProtocol(Protocol):

#     def add(self,       left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def multiply(self,  left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...


# @runtime_checkable
# class ArithmeticIterableBuilderProtocol(Protocol):

#     def add(self,       other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def multiply(self,  other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...

#     # Arithmetic operators
#     def __add__(self,       other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def __mul__(self,       other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...

#     # Reverse arithmetic operators (for when left operand is not ExpressionBuilder)
#     def __radd__(self,      other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def __rmul__(self,      other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
