"""Narwhals backend for mountainash struct operations."""
from __future__ import annotations

import narwhals as nw

from mountainash.expressions.backends.expression_systems.narwhals.base import NarwhalsBaseExpressionSystem
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
        if self.dialect == "narwhals-pyarrow":
            struct = self._arrow_struct(children)
        else:
            struct = nw.struct(**children)
        result = self._cast_target(struct, native)
        return nw.when(x.is_null()).then(nw.lit(None, dtype=native)).otherwise(result)

    @staticmethod
    def _arrow_struct(children: dict[str, nw.Expr]) -> nw.Expr:
        """Build a struct column with `pc.make_struct` on full-length Arrow arrays.

        `nw.struct` on PyArrow treats every length-1 operand as a broadcast
        scalar, which corrupts single-row frames; only genuine length mismatches
        are broadcast here.
        """
        import pyarrow as pa
        import pyarrow.compute as pc

        from .expsys_nw_ext_ma_scalar_value import _ElementwiseBatchExpr

        names = tuple(children)
        first, *rest = (child.alias(name) for name, child in children.items())

        def bind(source):
            namespace = source.__narwhals_namespace__()
            others = [expr._to_compliant_expr(namespace) for expr in rest]

            def evaluate(frame):
                head = source(frame)[0]
                series = [head, *(expr(frame)[0] for expr in others)]
                length = max(len(item) for item in series)
                arrays = [
                    item.native
                    if len(item) == length
                    else pa.repeat(item.native[0], length)
                    for item in series
                ]
                struct = pc.make_struct(*arrays, field_names=names)
                return [head._with_native(pa.chunked_array([struct]))]

            return source._from_callable(
                evaluate,
                evaluate_output_names=source._evaluate_output_names,
                alias_output_names=source._alias_output_names,
                context=source,
            )

        return _ElementwiseBatchExpr(
            first, None, None, native_polars=False, compliant_transform=bind,
        )

    def struct_field(self, x, /, *, field_name: str):
        return x.struct.field(field_name)
