"""Shared conform expression builder.

Builds expression lists from TypeSpec fields. Used by both
Relation.conform() and the DAG visitor's apply_conform.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec


def _build_conform_exprs(spec: "TypeSpec", source_columns: list[str]) -> list[Any]:
    """Build the expression list for a TypeSpec conformance projection.

    For each field in the spec, constructs an expression chain:
    col(source) -> coalesce(fill) -> cast(type) -> alias(target)

    When keep_only_mapped is False, appends col(name) for each source
    column not consumed by a mapped field.

    Args:
        spec: The TypeSpec describing the target schema.
        source_columns: Column names available in the source data.

    Returns:
        List of mountainash expressions ready for Relation.select().
    """
    import mountainash as ma
    from mountainash.typespec.universal_types import UniversalType
    from mountainash.typespec.type_bridge import bridge_type

    exprs: list[Any] = []
    mapped_sources: set[str] = set()

    for field in spec.fields:
        source_name = field.source_name

        if "." in source_name:
            parts = source_name.split(".")
            expr = ma.col(parts[0])
            for part in parts[1:]:
                expr = expr.struct.field(part)
            mapped_sources.add(parts[0])
        else:
            expr = ma.col(source_name)
            mapped_sources.add(source_name)

        if field.null_fill is not None:
            expr = ma.coalesce(expr, ma.lit(field.null_fill))

        if field.type and field.type != UniversalType.ANY:
            expr = expr.cast(bridge_type(field.type))

        expr = expr.name.alias(field.name)
        exprs.append(expr)

    if not spec.keep_only_mapped:
        for col in source_columns:
            if col not in mapped_sources:
                exprs.append(ma.col(col))

    return exprs
