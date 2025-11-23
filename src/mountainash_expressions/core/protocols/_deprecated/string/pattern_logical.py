# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_PATTERN_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes.string.string_expression_nodes import ExpressionNode, PatternExpressionNode, PatternLogicalExpressionNode
# if TYPE_CHECKING:
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_PATTERN_OPERATORS(Enum):
#     """
#     Enumeration for pattern matching operators.

#     Attributes:
#         - LIKE: SQL-style pattern matching (% and _ wildcards)
#         - REGEX_MATCH: Check if string matches regex pattern (full match)
#         - REGEX_CONTAINS: Check if string contains regex pattern
#     """

#     PAT_REGEX_REPLACE = auto()

#     PAT_LIKE = auto()
#     PAT_REGEX_MATCH = auto()
#     PAT_REGEX_CONTAINS = auto()


# class PatternLogicalVisitorProtocol(Protocol):

#     def visit_pattern_expression(self, node: PatternLogicalExpressionNode) -> SupportedExpressions: ...
#     def visit_pattern_logical_expression(self, node: PatternExpressionNode) -> SupportedExpressions: ...

#     def pat_regex_replace( self, node: PatternExpressionNode) -> SupportedExpressions: ...

#     def pat_like(self,           node: PatternLogicalExpressionNode) -> SupportedExpressions: ...
#     def pat_regex_match(self,    node: PatternLogicalExpressionNode) -> SupportedExpressions: ...
#     def pat_regex_contains(self, node: PatternLogicalExpressionNode) -> SupportedExpressions: ...


# class PatternLogicalExpressionProtocol(Protocol):

#     def pat_regex_replace( self, operand: SupportedExpressions, pattern: str, replacement: str, **kwargs) -> SupportedExpressions:   ...

#     def pat_like(self,           operand_expr: SupportedExpressions, pattern: str, **kwargs) -> SupportedExpressions: ...
#     def pat_regex_match(self,    operand_expr: SupportedExpressions, pattern: str, **kwargs) -> SupportedExpressions: ...
#     def pat_regex_contains(self, operand_expr: SupportedExpressions, pattern: str, **kwargs) -> SupportedExpressions: ...


# class PatternLogicalBuildersProtocol(Protocol):

#     def pat_regex_replace( self,  pattern: str, replacement: str, **kwargs) -> ExpressionBuilder:   ...

#     def pat_like(self,          pattern: str, **kwargs) -> ExpressionBuilder: ...
#     def pat_regex_match(self,   pattern: str, **kwargs) -> ExpressionBuilder: ...
#     def pat_regex_contains(self,pattern: str, **kwargs) -> ExpressionBuilder: ...
