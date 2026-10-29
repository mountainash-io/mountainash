"""Protocol for mountainash extension aggregate API builder methods."""
from __future__ import annotations

from typing import Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI


class MountainAshScalarAggregateAPIBuilderProtocol(Protocol):
    """Builder protocol for mountainash aggregate extensions."""

    def mean(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Short alias for avg()."""
        ...

    def n_unique(self) -> "BaseExpressionAPI":
        """Count distinct values."""
        ...
