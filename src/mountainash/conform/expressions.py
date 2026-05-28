"""Shared conform expression builder.

Builds expression lists from TypeSpec fields. Used by both
Relation.conform() and the DAG visitor's apply_conform.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec


def _build_conform_exprs(
    spec: "TypeSpec",
    *,
    available_columns: Optional[set[str]] = None,
) -> list[Any]:
    """Build the expression list for a TypeSpec conformance projection.

    For each field in the spec, constructs an expression chain:
    col(source) -> coalesce(fill) -> cast(type) -> alias(target)

    Produces exactly one expression per field in the spec. Unmapped source
    columns are not included — conform produces only what the spec defines.

    Args:
        spec: The TypeSpec describing the target schema.
        available_columns: When provided, fields whose source column is not
            in this set are silently skipped. Useful when the source data
            may not contain every column the spec describes (e.g. partial
            API responses).

    Returns:
        List of mountainash expressions ready for Relation.select().
    """
    exprs, _ = _build_conform_exprs_with_sources(
        spec, available_columns=available_columns,
    )
    return exprs


def _build_conform_exprs_with_sources(
    spec: "TypeSpec",
    *,
    available_columns: Optional[set[str]] = None,
) -> tuple[list[Any], set[str]]:
    """Build conform expressions and track which source columns were renamed.

    Returns:
        Tuple of (expressions, renamed_sources) where renamed_sources is the
        set of top-level source column names that were renamed to a different
        target name. Dotted sources (struct access) are excluded since the
        parent column may have other sub-fields in use.
    """
    import mountainash as ma
    from mountainash.typespec.universal_types import UniversalType
    from mountainash.typespec.type_bridge import bridge_type

    exprs: list[Any] = []
    renamed_sources: set[str] = set()

    for field in spec.fields:
        source_name = field.source_name

        if available_columns is not None:
            root_col = source_name.split(".")[0] if "." in source_name else source_name
            if root_col not in available_columns:
                continue

        is_dotted = "." in source_name
        if is_dotted:
            parts = source_name.split(".")
            expr = ma.col(parts[0])
            for part in parts[1:]:
                expr = expr.struct.field(part)
        else:
            expr = ma.col(source_name)
            if source_name != field.name:
                renamed_sources.add(source_name)

        if field.null_fill is not None:
            expr = ma.coalesce(expr, ma.lit(field.null_fill))

        if field.type and field.type != UniversalType.ANY:
            expr = expr.cast(bridge_type(field.type))

        expr = expr.name.alias(field.name)
        exprs.append(expr)

    return exprs, renamed_sources
