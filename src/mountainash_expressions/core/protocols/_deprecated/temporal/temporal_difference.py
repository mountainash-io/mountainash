# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_TEMPORAL_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, TemporalExpressionNode
# from ...expression_parameters import ExpressionParameter

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_TEMPORAL_DIFFERENCE_OPERATORS(Enum):
#     """
#     Enumeration for temporal/datetime operators.

#     Attributes:

#         Date Arithmetic (Difference):
#         - DIFF_DAYS: Calculate difference in days between dates
#         - DIFF_HOURS: Calculate difference in hours between datetimes
#         - DIFF_MINUTES: Calculate difference in minutes between datetimes
#         - DIFF_SECONDS: Calculate difference in seconds between datetimes
#         - DIFF_MONTHS: Calculate difference in months between dates
#         - DIFF_YEARS: Calculate difference in years between dates

#         Date Truncation:
#         - TRUNCATE: Truncate datetime to specified unit (day, hour, month, year, etc.)

#         Flexible Operations:
#         - OFFSET_BY: Add/subtract flexible duration using string format (e.g., "1d", "2h30m", "-3mo")
#     """

#     # Date Arithmetic - Difference
#     DT_DIFF_YEARS = auto()
#     DT_DIFF_MONTHS = auto()
#     DT_DIFF_DAYS = auto()
#     DT_DIFF_HOURS = auto()
#     DT_DIFF_MINUTES = auto()
#     DT_DIFF_SECONDS = auto()
#     DT_DIFF_MILLISECONDS = auto()



# class TemporalDifferenceVisitorProtocol(Protocol):

#     @property
#     def logic_type(self) -> CONST_LOGIC_TYPES: ...

#     # ===============
#     # Operations Maps
#     # ===============

#     def visit_temporal_difference_expression(self,     node: TemporalExpressionNode) -> Any: ...

#     def dt_diff_years(self,         node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_diff_months(self,        node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_diff_days(self,          node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_diff_hours(self,         node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_diff_minutes(self,       node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_diff_seconds(self,       node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_diff_milliseconds(self,  node: TemporalExpressionNode) -> SupportedExpressions: ...


# class TemporalDifferenceExpressionProtocol(Protocol):

#     def dt_diff_years(self,         left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_diff_months(self,        left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_diff_days(self,          left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_diff_hours(self,         left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_diff_minutes(self,       left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_diff_seconds(self,       left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_diff_milliseconds(self,  left_expr: SupportedExpressions, right_expr: SupportedExpressions) -> SupportedExpressions: ...

# class TemporaDifferencelBuilderProtocol(Protocol):

#     def dt_diff_years(self,         other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_diff_months(self,        other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_diff_days(self,          other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_diff_hours(self,         other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_diff_minutes(self,       other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_diff_seconds(self,       other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_diff_milliseconds(self,  other: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
