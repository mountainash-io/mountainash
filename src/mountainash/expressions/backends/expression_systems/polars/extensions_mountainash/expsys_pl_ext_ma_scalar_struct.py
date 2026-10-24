"""Polars backend for mountainash struct operations."""
from __future__ import annotations

import polars as pl

from mountainash.expressions.backends.expression_systems.polars.base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.core.dtypes import CastTarget, TypeTarget, registry
from ..numeric_cast import cast_container


class MountainAshPolarsScalarStructExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of struct field access."""
    def cast_struct(
        self,
        x,
        /,
        *converted_fields,
        dtype: CastTarget,
        field_names: tuple[str, ...] = (),
        failure_behavior: str = "throw",
    ):
        native = registry.to_native_cast(dtype, TypeTarget.POLARS)
        strict = failure_behavior != "null"
        if not converted_fields:
            return cast_container(x, native, strict=strict)
        result = cast_container(pl.struct([
            value.alias(name) for name, value in zip(field_names, converted_fields, strict=True)
        ]), native, strict=strict)
        return pl.when(x.is_null()).then(pl.lit(None, dtype=native)).otherwise(result)
    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
