"""Narwhals backend for mountainash struct operations."""
from __future__ import annotations

from collections.abc import Mapping
import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.core.dtypes import TypeTarget
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_STRUCT,
)


class MountainAshNarwhalsScalarStructExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of struct field access."""

    def cast_struct(
        self,
        x,
        /,
        *converted_fields,
        fields: Mapping[str, FieldSpec],
        failure_behavior: str = "throw",
    ):
        if failure_behavior == "null":
            raise BackendCapabilityError(
                "Narwhals cannot make an invalid nested field null the whole "
                "struct for failure_behavior='null'. Use Polars backend.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
            )
        if self.dialect == "narwhals-pandas":
            raise BackendCapabilityError(
                "Narwhals pandas struct casts cannot preserve null input structs.",
                backend=self.BACKEND_NAME,
                function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.CAST,
            )
        field = FieldSpec(fields=fields)
        dtype = _resolve_field_native(field, TypeTarget.NARWHALS, field_name="struct")
        if converted_fields:
            names = tuple(fields)
            validity = converted_fields[len(names)] if len(converted_fields) > len(names) else None
            result = nw.struct(
                **{
                    name: value
                    for name, value in zip(names, converted_fields[:len(names)], strict=True)
                }
            ).cast(dtype)
            result = nw.when(x.is_null()).then(nw.lit(None, dtype=dtype)).otherwise(result)
            if validity is not None:
                result = nw.when(validity).then(result).otherwise(nw.lit(None, dtype=dtype))
            return result
        return self._cast_target(x, dtype)

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)

