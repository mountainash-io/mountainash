"""Protocol for mountainash struct field operations."""
from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarStructExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for struct field access across backends."""

    def struct_field(self, x: ExpressionT, /, *, field_name: str) -> ExpressionT: ...
