# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_PATTERN_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, PatternExpressionNode
# from ...expression_parameters import ExpressionParameter

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_PATTERN_OPERATORS(Enum):
#     """
#     Enumeration for pattern matching operators.

#     Attributes:
#         - REGEX_REPLACE: Replace text using regex pattern
#     """
#     PAT_REGEX_REPLACE = auto()


# class PatternVisitorProtocol(Protocol):

#     def visit_pattern_expression(self, node: PatternExpressionNode) -> SupportedExpressions: ...
#     def pat_regex_replace( self, node: PatternExpressionNode) -> SupportedExpressions: ...

# class PatternExpressionsProtocol(Protocol):

#     def pat_regex_replace( self, operand: SupportedExpressions, pattern: str, replacement: str, **kwargs) -> SupportedExpressions:   ...


# class PatternBuilderProtocol(Protocol):

#     def pat_regex_replace( self,  pattern: str, replacement: str, **kwargs) -> ExpressionBuilder:   ...
