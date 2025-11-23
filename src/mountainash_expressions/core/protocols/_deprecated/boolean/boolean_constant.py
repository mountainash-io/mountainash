# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, List, Callable, Dict, TYPE_CHECKING
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto
# from ....types import SupportedExpressions

# from ...constants import CONST_EXPRESSION_LOGICAL_CONSTANT_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, LogicalConstantExpressionNode, LogicalExpressionNode, ComparisonExpressionNode, CollectionExpressionNode, UnaryExpressionNode
# from ...expression_builders.base_expression_builder import ExpressionBuilder
# from functools import reduce

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions


# class ENUM_BOOLEAN_CONSTANT_OPERATORS(Enum):
#     """
#     Enumeration for expression logical unary operators.
#     """
#     ALWAYS_TRUE = auto()
#     ALWAYS_FALSE = auto()

# class BooleanConstantVisitorProtocol(Protocol):

#     @property
#     def logic_type(self) -> CONST_LOGIC_TYPES: ...

#     def visit_boolean_constant_expression(self, node: LogicalConstantExpressionNode) -> SupportedExpressions: ...

#     def always_true(self) -> SupportedExpressions: ...
#     def always_false(self) -> SupportedExpressions: ...


# class BooleanConstantExpressionProtocol(Protocol):
#     def always_true(self) -> SupportedExpressions: ...
#     def always_false(self) -> SupportedExpressions: ...


# class BooleanConstantBuilderProtocol(Protocol):
#     def always_true(self) -> ExpressionBuilder: ...
#     def always_false(self) -> ExpressionBuilder: ...
