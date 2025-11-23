# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, List, Optional
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_TEMPORAL_OPERATORS, CONST_LOGIC_TYPES
# from .. import ExpressionVisitor
# from ...expression_nodes import ExpressionNode, TemporalExpressionNode, TemporalSnapshotExpressionNode
# from ...expression_parameters import ExpressionParameter
# if TYPE_CHECKING:
#     from ....types import SupportedExpressions

# class ENUM_TEMPORAL_LOGICAL_OPERATORS(Enum):
#     """
#     Enumeration for temporal/datetime operators.

#         Date Truncation:
#         - DT_TODAY: date truncated to day (i.e., current date at 00:00:00)
#         - DT_NOW: timestamp truncated to second (i.e., current date and time to nearest second)

#         # DT_IS_LEAP_YEAR = auto()
#         # DT_IS_WEEKEND = auto()
#         # DT_IS_WEEKDAY = auto()
#         # DT_IS_DAYLIGHT_SAVING = auto()


#     """
#     # Date/Time Extraction
#     DT_TODAY = auto()
#     DT_NOW = auto()


# class TemporalLogicalVisitorProtocol(Protocol):

#     @property
#     def logic_type(self) -> CONST_LOGIC_TYPES: ...

#     def visit_temporal_snapshot_expression(self, expression_node: TemporalSnapshotExpressionNode) -> SupportedExpressions: ...
#     def _process_temporal_snapshot_expression(self, operator: str, operand: TemporalExpressionNode) -> SupportedExpressions: ...

# class TemporalLogicalOperatorProtocol(Protocol):

#     @property
#     def temporal_ops(self) -> Dict[str, Callable]: ...

#     def dt_today(self) -> SupportedExpressions: ...
#     def dt_now(self) -> SupportedExpressions: ...


# class TemporalLogicalExpressionProtocol(Protocol):

#     def dt_today(self) -> SupportedExpressions: ...
#     def dt_now(self) -> SupportedExpressions: ...


# class TemporalLogicalBuilderProtocol(Protocol):

#     def dt_today(self) -> ExpressionBuilder: ...
#     def dt_now(self) -> ExpressionBuilder: ...
