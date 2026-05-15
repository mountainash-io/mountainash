"""Conform compiler — compiles TypeSpec to relation/expression operations."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.type_bridge import bridge_type

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec


def _get_source_columns(df: Any) -> list[str]:
    """Get column names from a native DataFrame without executing a relation."""
    if hasattr(df, "columns"):
        cols = df.columns
        if isinstance(cols, list):
            return cols
        return list(cols)
    if hasattr(df, "schema"):
        return list(df.schema().keys())
    raise ValueError(f"Cannot get columns from {type(df)}")


def _is_string_column(df: Any, col_name: str) -> bool:
    """Return True if the named column holds string/object data.

    Inspects the native DataFrame schema without triggering execution.
    Falls back to False (treat as non-string) on any error.
    """
    try:
        # Polars: df.schema is a dict-like of {col: dtype}
        # Narwhals: df.schema is similar
        if hasattr(df, "schema") and not callable(df.schema):
            dtype = df.schema[col_name]
            dtype_str = str(dtype).lower()
            return any(t in dtype_str for t in ("string", "utf8", "str", "object", "large_string"))

        # Ibis: df.schema() is callable and returns an ibis.Schema
        if hasattr(df, "schema") and callable(df.schema):
            dtype = df.schema()[col_name]
            dtype_str = str(dtype).lower()
            return any(t in dtype_str for t in ("string", "utf8", "str", "object"))

    except Exception:
        pass

    return False


def compile_conform(spec: TypeSpec, df: Any) -> Any:
    """Compile a TypeSpec conformance plan to relation operations and execute.

    Walks the TypeSpec fields and builds a single relation projection:
    - Applies coalesce for null_fill (before cast, to avoid pandas NaN→int errors)
    - Applies cast via the type bridge (UniversalType → MountainashDtype)
    - Applies name.alias to rename to the target column name
    - Passes through unmapped columns when keep_only_mapped is False

    The null_fill value is represented as a string literal when the source column
    is string-typed and the fill is numeric — this is required by Ibis, which
    enforces strict type precedence in coalesce() and cannot mix string and numeric
    operands.  All other backends (Polars, Narwhals) handle the subsequent cast
    from the string fill to the target numeric dtype without issue.

    Args:
        spec: The TypeSpec describing the target schema.
        df: A native DataFrame (Polars, pandas/narwhals, or Ibis table).

    Returns:
        A Polars DataFrame with the conformed data.
    """
    import mountainash as ma
    from mountainash.core.dtypes import MountainashDtype

    _NUMERIC_DTYPES = {
        MountainashDtype.I8, MountainashDtype.I16,
        MountainashDtype.I32, MountainashDtype.I64,
        MountainashDtype.FP32, MountainashDtype.FP64,
    }

    r = ma.relation(df)
    source_columns = _get_source_columns(df)

    mapped_exprs = []
    mapped_source_names: set[str] = set()

    for field in spec.fields:
        source_name = field.source_name
        mapped_source_names.add(source_name.split(".")[0] if "." in source_name else source_name)

        if "." in source_name:
            parts = source_name.split(".")
            expr = ma.col(parts[0])
            for part in parts[1:]:
                expr = expr.struct.field(part)
        else:
            expr = ma.col(source_name)

        has_cast = bool(field.type and field.type != UniversalType.ANY)
        dtype = bridge_type(field.type) if has_cast else None

        # Null fill before cast — this ordering matches the established pattern
        # (fill → cast) and avoids pandas IntCastingNaNError when a nullable-int
        # source column is stored as float64 (pandas representation of int+None).
        #
        # Ibis enforces strict type precedence in coalesce(): it cannot mix a
        # string column operand with a numeric literal.  When the source column is
        # string-typed and the target is numeric, we therefore represent the fill
        # as its string form (e.g. "-1" instead of -1).  Polars and Narwhals cast
        # the resulting string-filled expression to the target dtype in the next
        # step without issue.
        if field.null_fill is not None:
            fill_value = field.null_fill
            if (
                has_cast
                and dtype in _NUMERIC_DTYPES
                and isinstance(fill_value, (int, float))
                and _is_string_column(df, source_name)
            ):
                fill_value = str(fill_value)
            expr = ma.coalesce(expr, ma.lit(fill_value))

        # Cast after filling so the target dtype applies to an already-filled
        # expression (no NaN remaining in integer-destination columns).
        if has_cast:
            expr = expr.cast(dtype)

        # Rename: alias the expression output to the target column name
        expr = expr.name.alias(field.name)
        mapped_exprs.append(expr)

    # Pass through unmapped columns unchanged when keep_only_mapped is False
    if not spec.keep_only_mapped:
        for col_name in source_columns:
            if col_name not in mapped_source_names:
                mapped_exprs.append(ma.col(col_name))

    return r.select(*mapped_exprs).to_polars()
