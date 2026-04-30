"""AST-level schema inference for relation node trees.

Walks the relation AST to extract {column_name: type} without compilation
or backend involvement. Types come from the source data (DataFrames,
DataResource schemas); column names come from the AST structure.
"""
from __future__ import annotations

from typing import Any, Optional

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_NAME,
)


def infer_expression_name(expr_node: Any) -> Optional[str]:
    """Extract the output column name from an expression node tree.

    Returns the alias name if the expression is wrapped in an ALIAS node,
    the field name if it's a bare FieldReferenceNode, or None if the name
    cannot be determined.
    """
    from mountainash.expressions.core.expression_nodes import (
        FieldReferenceNode,
        ScalarFunctionNode,
    )

    if isinstance(expr_node, FieldReferenceNode):
        return expr_node.field

    if isinstance(expr_node, ScalarFunctionNode):
        fk = expr_node.function_key
        if fk == FKEY_MOUNTAINASH_NAME.ALIAS:
            return expr_node.options.get("name")
        if fk == FKEY_MOUNTAINASH_NAME.PREFIX:
            inner_name = infer_expression_name(expr_node.arguments[0])
            prefix = expr_node.options.get("prefix", "")
            return f"{prefix}{inner_name}" if inner_name else None
        if fk == FKEY_MOUNTAINASH_NAME.SUFFIX:
            inner_name = infer_expression_name(expr_node.arguments[0])
            suffix = expr_node.options.get("suffix", "")
            return f"{inner_name}{suffix}" if inner_name else None
        if fk == FKEY_MOUNTAINASH_NAME.NAME_TO_UPPER:
            inner_name = infer_expression_name(expr_node.arguments[0])
            return inner_name.upper() if inner_name else None
        if fk == FKEY_MOUNTAINASH_NAME.NAME_TO_LOWER:
            inner_name = infer_expression_name(expr_node.arguments[0])
            return inner_name.lower() if inner_name else None

    return None


def _schema_from_dataframe(df: Any) -> dict[str, Any]:
    """Extract schema from a native dataframe.

    Supports Polars DataFrame/LazyFrame. Returns {} for unrecognized types.
    Isolated for future refinement (narwhals, pandas, etc.).
    """
    if hasattr(df, "collect_schema"):
        polars_schema = df.collect_schema()
        return dict(zip(polars_schema.names(), polars_schema.dtypes()))
    if hasattr(df, "schema") and not callable(df.schema):
        return dict(df.schema)
    if hasattr(df, "schema") and callable(df.schema):
        schema_obj = df.schema()
        if hasattr(schema_obj, "items"):
            return dict(schema_obj)
    return {}


def _schema_from_table_schema(table_schema: dict) -> dict[str, Any]:
    """Extract schema from a Frictionless table_schema dict.

    Returns {field_name: type_string}. Isolated for future refinement.
    """
    fields = table_schema.get("fields", [])
    if not fields:
        return {}
    return {f["name"]: f.get("type", "unknown") for f in fields}
