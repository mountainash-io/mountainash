"""Protocol for mountainash extension aggregate operations."""
from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class MountainashExtensionAggregateExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for mountainash extension aggregate operations."""

    def n_unique(self, x: ExpressionT, /) -> ExpressionT:
        """Count distinct values."""
        ...
