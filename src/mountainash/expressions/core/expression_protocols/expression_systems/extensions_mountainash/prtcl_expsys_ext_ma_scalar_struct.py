"""Protocol for mountainash struct field operations."""
from __future__ import annotations

from typing import Protocol, Literal

from mountainash.core.types import ExpressionT
from mountainash.core.dtypes import CastTarget  # noqa: TC001 - runtime get_type_hints() resolution


class MountainAshScalarStructExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for struct field access across backends."""

    def struct_field(self, x: ExpressionT, /, *, field_name: str) -> ExpressionT: ...
    def cast_struct(
        self,
        x: ExpressionT,
        /,
        *converted_fields: ExpressionT,
        dtype: CastTarget,
        field_names: tuple[str, ...] = (),
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> ExpressionT: ...
