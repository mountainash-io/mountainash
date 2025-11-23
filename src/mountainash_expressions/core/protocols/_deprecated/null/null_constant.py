
# from __future__ import annotations
# from typing import Callable, TYPE_CHECKING, Dict, Any, List
# from abc import ABC, abstractmethod
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto
# from ....types import SupportedExpressions

# from ...constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS, CONST_EXPRESSION_SOURCE_OPERATORS

# if TYPE_CHECKING:
#     from ...expression_nodes import ExpressionNode, NullConstantExpressionNode
#     from ...expression_parameters import ExpressionParameter
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_NULL_CONSTANT_OPERATORS(Enum):
#     """
#     Enumeration for pattern matching operators.

#     Attributes:
#         - LIKE: SQL-style pattern matching (% and _ wildcards)
#         - REGEX_MATCH: Check if string matches regex pattern (full match)
#         - REGEX_CONTAINS: Check if string contains regex pattern
#         - REGEX_REPLACE: Replace text using regex pattern
#     """
#     ALWAYS_NULL = auto()


# class NullConstantVisitorProtocol(Protocol):

#     def visit_null_constant_expression(self, node: NullConstantExpressionNode) -> SupportedExpressions: ...
#     def always_null(self) -> SupportedExpressions: ...

# class NullConstantExpressionProtocol(Protocol):

#     def always_null(self) -> SupportedExpressions: ...

# class NullConstantBuilderProtocol(Protocol):

#     def always_null(self) -> ExpressionBuilder: ...
