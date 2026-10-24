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
