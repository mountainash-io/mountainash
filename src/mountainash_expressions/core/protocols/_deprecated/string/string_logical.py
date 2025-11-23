# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_STRING_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, StringExpressionNode
# from ...expression_parameters import ExpressionParameter

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_STRING_LOGICAL_OPERATORS(Enum):
#     """
#     Enumeration for string operators.

#     Attributes:
#         - STR_CONTAINS: Check if string contains substring
#         - STR_STARTS_WITH: Check if starts with prefix
#         - STR_ENDS_WITH: Check if ends with suffix
#     """
#     STR_CONTAINS = auto()
#     STR_STARTS_WITH = auto()
#     STR_ENDS_WITH = auto()


# class StringLogicalVisitorProtocol(Protocol):

#     def visit_string_expression(self, node: StringExpressionNode) -> Any: ...

#     # String checks (return boolean)
#     def str_contains(self,      node: StringExpressionNode) -> SupportedExpressions: ...
#     def str_starts_with(self,   node: StringExpressionNode) -> SupportedExpressions: ...
#     def str_ends_with(self,     node: StringExpressionNode) -> SupportedExpressions: ...


# class StringLogicalExpressionProtocol(Protocol):

#     # String checks (return boolean)
#     def str_contains(self,      operand_expr: SupportedExpressions, substring: Any, **kwargs) -> SupportedExpressions: ...
#     def str_starts_with(self,   operand_expr: SupportedExpressions, prefix: Any, **kwargs) -> SupportedExpressions: ...
#     def str_ends_with(self,     operand_expr: SupportedExpressions, suffix: Any, **kwargs) -> SupportedExpressions: ...

# class StringLogicalBuilderProtocol(Protocol):

#     # String checks (return boolean)
#     def str_contains(self,      substring: Any, **kwargs) -> ExpressionBuilder: ...
#     def str_starts_with(self,   prefix: Any, **kwargs) -> ExpressionBuilder: ...
#     def str_ends_with(self,     suffix: Any, **kwargs) -> ExpressionBuilder: ...
