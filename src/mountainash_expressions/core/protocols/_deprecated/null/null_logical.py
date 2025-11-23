
# from __future__ import annotations
# from typing import Callable, TYPE_CHECKING, Dict, Any, List
# from abc import ABC, abstractmethod
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto
# from ....types import SupportedExpressions

# from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS, CONST_EXPRESSION_SOURCE_OPERATORS

# if TYPE_CHECKING:
#     from ...expression_nodes import ExpressionNode, NullLogicalExpressionNode
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_NULL_LOGICAL_OPERATORS(Enum):
#     """
#     Enumeration for pattern matching operators.

#     Attributes:
#         - LIKE: SQL-style pattern matching (% and _ wildcards)
#         - REGEX_MATCH: Check if string matches regex pattern (full match)
#         - REGEX_CONTAINS: Check if string contains regex pattern
#         - REGEX_REPLACE: Replace text using regex pattern
#     """
#     IS_NULL = auto()
#     NOT_NULL = auto()


# class NullLogicalVisitorProtocol(Protocol):

#     def visit_null_logical_expression(self, node: NullLogicalExpressionNode) -> Any: ...

#     def is_null(self, node: NullLogicalExpressionNode) -> Any: ...
#     def not_null(self, node: NullLogicalExpressionNode) -> Any: ...


# class NullLogicalExpressionProtocol(Protocol):

#     def is_null(self, operand: SupportedExpressions) -> SupportedExpressions: ...
#     def not_null(self, operand: SupportedExpressions) -> SupportedExpressions: ...


# class NullLogicalBuilderProtocol(Protocol):

#     def is_null(self) -> ExpressionBuilder: ...
#     def not_null(self) -> ExpressionBuilder: ...
