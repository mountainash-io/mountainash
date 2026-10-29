"""Protocol for Mountainash categorical operations."""
from __future__ import annotations

from typing import Any, Literal, Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarCategoricalExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for categorical casts across backends."""

    def cast_categorical(
        self,
        x: ExpressionT,
        /,
        *,
        value_type: str,
        categories: tuple[Any, ...],
        ordered: bool,
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> ExpressionT: ...
