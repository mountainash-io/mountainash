# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_TEMPORAL_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import ExpressionNode, TemporalExpressionNode
# from ...expression_parameters import ExpressionParameter

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_TEMPORAL_MODIFICATION_OPERATORS(Enum):
#     """
#     Enumeration for temporal/datetime operators.

#     Attributes:

#         Date Arithmetic (Add):
#         - ADD_DAYS: Add days to a date
#         - ADD_HOURS: Add hours to a datetime
#         - ADD_MINUTES: Add minutes to a datetime
#         - ADD_SECONDS: Add seconds to a datetime
#         - ADD_MONTHS: Add months to a date
#         - ADD_YEARS: Add years to a date


#         # DT_AS_UTC = auto()
#         # DT_AS_LOCAL_TZ = auto()


#         Date Truncation:
#         - TRUNCATE: Truncate datetime to specified unit (day, hour, month, year, etc.)

#         Flexible Operations:
#         - OFFSET_BY: Add/subtract flexible duration using string format (e.g., "1d", "2h30m", "-3mo")
#     """

#     # Date Arithmetic - Modification
#     DT_ADD_DAYS = auto()
#     DT_ADD_HOURS = auto()
#     DT_ADD_MINUTES = auto()
#     DT_ADD_SECONDS = auto()
#     DT_ADD_MONTHS = auto()
#     DT_ADD_YEARS = auto()

#     # Date Truncation
#     DT_TRUNCATE = auto()

#     # Flexible Operations
#     DT_OFFSET_BY = auto()




# class TemporalModificationVisitorProtocol(Protocol):

#     @property
#     def logic_type(self) -> CONST_LOGIC_TYPES: ...

#     def visit_temporal_expression(self,     node: TemporalExpressionNode) -> Any: ...

#     def dt_add_days(self,   node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_add_hours(self,  node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_add_minutes(self,node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_add_seconds(self,node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_add_months(self, node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_add_years(self,  node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_truncate(self,   node: TemporalExpressionNode) -> SupportedExpressions: ...
#     def dt_offset_by(self,  node: TemporalExpressionNode) -> SupportedExpressions: ...


# class TemporalModificationExpressionProtocol(Protocol):

#     def dt_add_days(self,   operand_expr: SupportedExpressions, days_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_add_hours(self,  operand_expr: SupportedExpressions, hours_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_add_minutes(self,operand_expr: SupportedExpressions, minutes_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_add_seconds(self,operand_expr: SupportedExpressions, seconds_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_add_months(self, operand_expr: SupportedExpressions, months_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_add_years(self,  operand_expr: SupportedExpressions, years_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_truncate(self,   operand_expr: SupportedExpressions, unit_expr: SupportedExpressions) -> SupportedExpressions: ...
#     def dt_offset_by(self,  operand_expr: SupportedExpressions, offset_expr: SupportedExpressions) -> SupportedExpressions: ...


# class TemporalModificationBuilderProtocol(Protocol):

#     def dt_add_days(self,   days: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_add_hours(self,  hours: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_add_minutes(self,minutes: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_add_seconds(self,seconds: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_add_months(self, months: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_add_years(self,  years: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...

#     def dt_truncate(self,   unit: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
#     def dt_offset_by(self,  offset: Union[ExpressionBuilder,ExpressionNode, Any]) -> ExpressionBuilder: ...
