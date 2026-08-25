"""Protocol for mountainash struct field operations."""
from __future__ import annotations

from typing import Protocol, Literal

from mountainash.core.types import ExpressionT
from mountainash.typespec.spec import FieldSpec  # noqa: TCH002


class MountainAshScalarStructExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for struct field access across backends."""

    def struct_field(self, x: ExpressionT, /, *, field_name: str) -> ExpressionT: ...
    def cast_struct(
        self,
        x: ExpressionT,
        /,
        *,
        fields: tuple[FieldSpec, ...],
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> ExpressionT: ...
