"""Protocol for mountainash struct field operations."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, Literal

from mountainash.core.types import ExpressionT
from mountainash.typespec.spec import FieldSpec  # noqa: TC001 - runtime get_type_hints() resolution


class MountainAshScalarStructExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for struct field access across backends."""

    def struct_field(self, x: ExpressionT, /, *, field_name: str) -> ExpressionT: ...
    def cast_struct(
        self,
        x: ExpressionT,
        /,
        *converted_fields: ExpressionT,
        fields: Mapping[str, FieldSpec],
        failure_behavior: Literal["throw", "null"] = "throw",
    ) -> ExpressionT: ...
