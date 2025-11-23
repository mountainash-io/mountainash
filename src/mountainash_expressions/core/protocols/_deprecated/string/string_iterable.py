# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING, Union
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_STRING_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, StringExpressionNode
# from ...expression_parameters import ExpressionParameter

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_STRING_ITERABLE_OPERATORS(Enum):
#     """
#     Enumeration for string operators.

#     Attributes:
#         - STR_CONCAT: Concatenate strings
#     """
#     STR_CONCAT = auto()


# class StringIterableVisitorProtocol(Protocol):

#     def visit_string_iterable_expression(self, node: StringIterableExpressionNode) -> Any: ...
#     def str_concat(self, node: StringIterableExpressionNode) -> SupportedExpressions: ...



# class StringIterableExpressionProtocol(Protocol):

#     def str_concat(self, operand_expr: SupportedExpressions, *others: Any, **kwargs) -> SupportedExpressions: ...

# class StringIterableBuilderProtocol(Protocol):

#     def str_concat(self, *others: Union[ExpressionBuilder,ExpressionNode, Any], **kwargs) -> ExpressionBuilder: ...
