"""Planning-time replacement for Polars' removed String-to-temporal casts."""
from __future__ import annotations

import polars as pl


def contains_temporal(dtype) -> bool:
    if dtype.base_type() in (pl.Date, pl.Datetime, pl.Time):
        return True
    if isinstance(dtype, (pl.List, pl.Array)):
        return contains_temporal(dtype.inner)
    if isinstance(dtype, pl.Struct):
        return any(contains_temporal(field.dtype) for field in dtype.fields)
    return False


def cast_temporal_compatible(x, dtype, *, strict):
    """Keep native casts except where String leaves require temporal parsing."""
    if not contains_temporal(dtype):
        return x.cast(dtype, strict=strict)
    return x.pipe_with_dtype(lambda expr, source: _cast(expr, source, dtype, strict))


def _cast(x, source, target, strict):
    if target is pl.Datetime:
        target = pl.Datetime()
    if source == pl.String:
        if target == pl.Date:
            return x.str.to_date("%Y-%m-%d", strict=strict)
        if target == pl.Time:
            return x.str.to_time("%H:%M:%S%.f", strict=strict)
        if isinstance(target, pl.Datetime):
            # A naive cast preserves wall-clock fields even for offset-bearing text.
            # A zoned cast requires an explicit input offset and preserves its instant.
            text = x
            if target.time_zone is None:
                text = text.str.replace(r"(?:Z|[+-]\d{2}:?\d{2})$", "")
            text = text.str.replace(
                r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(Z|[+-]\d{2}:?\d{2})?$",
                "${1}:00${2}",
            )
            fmt = "%Y-%m-%dT%H:%M:%S%.f"
            if target.time_zone is not None:
                fmt += "%#z"
            return text.str.to_datetime(
                fmt, time_unit=target.time_unit, time_zone=target.time_zone,
                strict=strict,
            )
    if isinstance(source, (pl.List, pl.Array)) and isinstance(target, (pl.List, pl.Array)):
        element = _cast(pl.element(), source.inner, target.inner, strict)
        if isinstance(source, pl.Array):
            converted = x.arr.eval(element)
        else:
            converted = x.list.eval(element)
        return converted.cast(target, strict=strict)
    if isinstance(source, pl.Struct) and isinstance(target, pl.Struct):
        source_fields = dict(source.to_schema())
        fields = [
            _cast(x.struct.field(field.name), source_fields[field.name], field.dtype, strict).alias(field.name)
            if field.name in source_fields else pl.lit(None, dtype=field.dtype).alias(field.name)
            for field in target.fields
        ]
        return pl.when(x.is_null()).then(pl.lit(None, dtype=target)).otherwise(
            pl.struct(fields)
        ).alias(x.meta.output_name(raise_if_undetermined=False) or "")
    return x.cast(target, strict=strict)
