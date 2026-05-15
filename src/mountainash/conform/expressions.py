"""Shared conform expression builder.

Builds expression lists from TypeSpec fields. Used by both
Relation.conform() and the DAG visitor's apply_conform.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec


def _build_conform_exprs(spec: "TypeSpec") -> list[Any]:
    """Build the expression list for a TypeSpec conformance projection.

    For each field in the spec, constructs an expression chain:
    col(source) -> coalesce(fill) -> cast(type) -> alias(target)

    Produces exactly one expression per field in the spec. Unmapped source
    columns are not included — conform produces only what the spec defines.

    Args:
        spec: The TypeSpec describing the target schema.

    Returns:
        List of mountainash expressions ready for Relation.select().
    """
    import mountainash as ma
    from mountainash.typespec.universal_types import UniversalType
    from mountainash.typespec.type_bridge import bridge_type

    exprs: list[Any] = []

    for field in spec.fields:
        source_name = field.source_name

        if "." in source_name:
            parts = source_name.split(".")
            expr = ma.col(parts[0])
            for part in parts[1:]:
                expr = expr.struct.field(part)
        else:
            expr = ma.col(source_name)

        if field.null_fill is not None:
            expr = ma.coalesce(expr, ma.lit(field.null_fill))

        if field.type and field.type != UniversalType.ANY:
            expr = expr.cast(bridge_type(field.type))

        expr = expr.name.alias(field.name)
        exprs.append(expr)

    return exprs
