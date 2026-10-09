"""Narwhals backend for mountainash struct operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.core.dtypes import TypeTarget
from mountainash.core.dtypes.numeric import has_nested_numeric_fields
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from mountainash.typespec.converters import _resolve_field_native
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.universal_types import UniversalType


class MountainAshNarwhalsScalarStructExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarStructExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of struct field access."""

    def cast_struct(
        self,
        x,
        /,
        *,
        fields: tuple[FieldSpec, ...],
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
        field = FieldSpec(name="_struct", type=UniversalType.OBJECT, object_fields=list(fields))
        dtype = _resolve_field_native(field, TypeTarget.NARWHALS)
        if has_nested_numeric_fields(fields):
            from mountainash.expressions.backends.expression_systems.narwhals.extensions_mountainash.expsys_nw_ext_ma_scalar_value import (
                _polars_elementwise_batches,
            )
            from mountainash.expressions.backends.expression_systems.polars.extensions_mountainash.expsys_pl_ext_ma_scalar_struct import (
                _convert_struct_batch,
            )

            native_dtype = _resolve_field_native(field, TypeTarget.POLARS)

            def convert_batch(batch):
                return _convert_struct_batch(batch, field, native_dtype, failure_behavior)

            return _polars_elementwise_batches(x, convert_batch, native_dtype)
        return x.cast(dtype)

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
