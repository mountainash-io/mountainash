"""Float32 conversion validity for Polars-native expressions.

Polars' `cast(Float32)` turns a finite Float64 beyond the Float32 range into
infinity without raising. Integer casts already raise (strict) or null
(non-strict) natively, so only this conversion needs a validity predicate.
"""
from __future__ import annotations

import polars as pl


def cast_float32_checked(x: pl.Expr, source: pl.DataType, *, strict: bool) -> pl.Expr:
    """Cast to Float32, treating newly created infinity as an invalid conversion.

    Existing NaN/infinity/null inputs and ordinary rounding (including a value
    that rounds down to the Float32 maximum) are not invalid. Strict conversion
    raises at execution; non-strict conversion yields a typed null.
    """
    candidate = x.cast(pl.Float32, strict=strict)
    if source != pl.Float64:
        return candidate
    invalid = (x.is_finite() & ~candidate.is_finite()).fill_null(False)
    null = pl.lit(None, dtype=pl.Float32)
    if not strict:
        return pl.when(~invalid).then(candidate).otherwise(null)
    # Exhaustive over the valid value: a true predicate has no replacement and raises.
    return pl.when(invalid.replace_strict({False: True}, return_dtype=pl.Boolean)).then(candidate).otherwise(null)


def _has_float32(dtype) -> bool:
    if dtype == pl.Float32:
        return True
    if isinstance(dtype, (pl.List, pl.Array)):
        return _has_float32(dtype.inner)
    if isinstance(dtype, pl.Struct):
        return any(_has_float32(field.dtype) for field in dtype.fields)
    return False


def _items(x: pl.Expr, source: pl.DataType, body: pl.Expr) -> pl.Expr:
    return x.arr.eval(body) if isinstance(source, pl.Array) else x.list.eval(body)


def convert_native(x: pl.Expr, source: pl.DataType, target: pl.DataType, *, strict: bool) -> pl.Expr:
    """Convert to a complete native target, applying scalar validity at every depth.

    Native strict/try casts are used wherever they are sufficient; only subtrees
    that reach Float32 are rebuilt so the scalar Float32 validity applies to
    nested leaves. The original `target` (with its refinements) is the final cast.
    """
    from .temporal_cast import cast_temporal_compatible

    if not _has_float32(target):
        return cast_temporal_compatible(x, target, strict=strict)
    if target == pl.Float32:
        return cast_float32_checked(x, source, strict=strict)
    if isinstance(source, (pl.List, pl.Array)) and isinstance(target, (pl.List, pl.Array)):
        element = convert_native(pl.element(), source.inner, target.inner, strict=strict)
        return _items(x, source, element).cast(target, strict=strict)
    if isinstance(source, pl.Struct) and isinstance(target, pl.Struct):
        source_fields = dict(source.to_schema())
        fields = [
            convert_native(x.struct.field(f.name), source_fields[f.name], f.dtype, strict=strict).alias(f.name)
            if f.name in source_fields else pl.lit(None, dtype=f.dtype).alias(f.name)
            for f in target.fields
        ]
        rebuilt = pl.struct(fields).cast(target, strict=strict)
        return pl.when(x.is_null()).then(pl.lit(None, dtype=target)).otherwise(rebuilt)
    return cast_temporal_compatible(x, target, strict=strict)


def invalid_conversion(x: pl.Expr, source: pl.DataType, target: pl.DataType) -> pl.Expr:
    """True where a non-null value (at any depth) fails the non-strict conversion."""
    if isinstance(source, (pl.List, pl.Array)) and isinstance(target, (pl.List, pl.Array)):
        item = invalid_conversion(pl.element(), source.inner, target.inner)
        evaluated = _items(x, source, item)
        anyed = evaluated.arr.any() if isinstance(source, pl.Array) else evaluated.list.any()
        return x.is_not_null() & anyed.fill_null(False)
    if isinstance(source, pl.Struct) and isinstance(target, pl.Struct):
        source_fields = dict(source.to_schema())
        invalid = pl.lit(False)
        for f in target.fields:
            if f.name in source_fields:
                invalid = invalid | invalid_conversion(
                    x.struct.field(f.name), source_fields[f.name], f.dtype,
                )
        return x.is_not_null() & invalid.fill_null(False)
    return x.is_not_null() & convert_native(x, source, target, strict=False).is_null()


def cast_container(x: pl.Expr, target: pl.DataType, *, strict: bool) -> pl.Expr:
    """Direct container cast; under non-strict, any invalid nested value nulls the whole container."""
    def build(expr: pl.Expr, source: pl.DataType) -> pl.Expr:
        result = convert_native(expr, source, target, strict=strict)
        if strict:
            return result
        invalid = invalid_conversion(expr, source, target)
        return pl.when(expr.is_null()).then(None).when(invalid).then(None).otherwise(result)
    return x.pipe_with_dtype(build)
