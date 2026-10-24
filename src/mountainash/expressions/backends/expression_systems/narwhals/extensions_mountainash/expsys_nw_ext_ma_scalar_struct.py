"""Narwhals backend for mountainash struct operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
from mountainash.expressions.backends.expression_systems.narwhals.numeric_cast import checked_struct
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarStructExpressionSystemProtocol
from mountainash.core.dtypes import CastTarget, TypeTarget, registry
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
        dtype: CastTarget,
        field_names: tuple[str, ...] = (),
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
        if not converted_fields:
            return self.cast(x, dtype=dtype, failure_behavior=failure_behavior)
        native = registry.to_native_cast(dtype, TypeTarget.NARWHALS)
        children = dict(zip(field_names, converted_fields, strict=True))
        if isinstance(native, nw.Struct):
            # Each converted child is checked from its own output dtype (argument
            # positions 1..n), so narrowing that survived conversion is still rejected.
            members = {}
            for position, (name, child) in enumerate(children.items(), start=1):
                evidence = self.native_operand_type(position)
                members[name] = (child, None if evidence is None else evidence.native_dtype)
            checked = checked_struct(x, native, members, self._cast_target)
            if checked is not None:
                return checked
        result = self._cast_target(nw.struct(**children), native)
        return nw.when(x.is_null()).then(nw.lit(None, dtype=native)).otherwise(result)

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
