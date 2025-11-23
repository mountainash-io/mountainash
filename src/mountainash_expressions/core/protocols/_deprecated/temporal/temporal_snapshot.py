# from __future__ import annotations
# from abc import abstractmethod
# from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
# from typing import Protocol, runtime_checkable
# from enum import Enum, auto

# from ...constants import CONST_EXPRESSION_TEMPORAL_OPERATORS, CONST_LOGIC_TYPES
# from ...expression_nodes import TemporalSnapshotExpressionNode
# from ...expression_parameters import ExpressionParameter

# if TYPE_CHECKING:
#     from ....types import SupportedExpressions
#     from ...expression_builders.base_expression_builder import ExpressionBuilder


# class ENUM_TEMPORAL_SNAPSHOT_OPERATORS(Enum):
#     """
#     Enumeration for temporal/datetime operators.

#         Date Truncation:
#         - DT_TODAY: date truncated to day (i.e., current date at 00:00:00)
#         - DT_NOW: timestamp truncated to second (i.e., current date and time to nearest second)

#     """
#     # Date/Time Extraction
#     DT_TODAY = auto()
#     DT_NOW = auto()


# class TemporalSnapshotVisitorProtocol(Protocol):

#     @property
#     def logic_type(self) -> CONST_LOGIC_TYPES: ...

#     def visit_temporal_snapshot_expression(self, node: TemporalSnapshotExpressionNode) -> SupportedExpressions: ...

#     def dt_today(self) -> SupportedExpressions: ...
#     def dt_now(self) -> SupportedExpressions: ...


# class TemporalSnapshotExpressionProtocol(Protocol):

#     def dt_today(self) -> SupportedExpressions: ...
#     def dt_now(self) -> SupportedExpressions: ...


# class TemporalSnapshotBuilderProtocol(Protocol):

#     def dt_today(self) -> ExpressionBuilder: ...
#     def dt_now(self) -> ExpressionBuilder: ...
