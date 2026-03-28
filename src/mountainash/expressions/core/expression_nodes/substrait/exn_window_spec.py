"""Window specification value objects.

WindowSpec defines the partitioning, ordering, and frame bounds for window functions.
WindowBound defines individual frame bounds (preceding, following, current row).

These are value objects (not AST nodes) — they don't participate in the visitor pattern.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

from mountainash.core.constants import SortField, WindowBoundType


class WindowBound(BaseModel, frozen=True):
    """Frame bound specification for window functions.

    Examples:
        WindowBound(bound_type=WindowBoundType.CURRENT_ROW)
        WindowBound(bound_type=WindowBoundType.PRECEDING, offset=3)
        WindowBound(bound_type=WindowBoundType.UNBOUNDED_PRECEDING)
    """
    model_config = ConfigDict(frozen=True)

    bound_type: WindowBoundType
    offset: Optional[int] = None


class WindowSpec(BaseModel, frozen=True):
    """Window specification: partitioning, ordering, and frame bounds.

    Shared by WindowFunctionNode and OverNode. Built by the .over() method.

    Attributes:
        partition_by: Grouping expressions (FieldReferenceNodes or raw column names).
        order_by: Sort specifications using existing SortField dataclass.
        lower_bound: Frame lower bound (None = start of partition).
        upper_bound: Frame upper bound (None = end of partition).
    """
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
    )

    partition_by: list[Any] = []
    order_by: list[SortField] = []
    lower_bound: Optional[WindowBound] = None
    upper_bound: Optional[WindowBound] = None
