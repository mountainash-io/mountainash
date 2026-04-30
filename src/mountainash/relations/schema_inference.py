"""AST-level schema inference for relation node trees.

Walks the relation AST to extract {column_name: type} without compilation
or backend involvement. Types come from the source data (DataFrames,
DataResource schemas); column names come from the AST structure.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

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


def infer_schema(
    node: Any,
    ref_resolver: Optional[Callable[[str], dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Walk a RelationNode tree and return {column_name: type} without compilation."""
    from mountainash.relations.core.relation_nodes.substrait import (
        ReadRelNode,
        FilterRelNode,
        SortRelNode,
        FetchRelNode,
        ProjectRelNode,
        AggregateRelNode,
        JoinRelNode,
        SetRelNode,
    )
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        RefRelNode,
        ResourceReadRelNode,
        SourceRelNode,
        ExtensionRelNode,
    )

    # --- Leaf nodes ---
    if isinstance(node, ReadRelNode):
        return _schema_from_dataframe(node.dataframe)

    if isinstance(node, RefRelNode):
        if ref_resolver is not None:
            return ref_resolver(node.name)
        return {}

    if isinstance(node, ResourceReadRelNode):
        ts = node.resource.table_schema
        if isinstance(ts, dict):
            return _schema_from_table_schema(ts)
        return {}

    if isinstance(node, SourceRelNode):
        return _schema_from_source_data(node.data)

    # --- Pass-through nodes ---
    if isinstance(node, (FilterRelNode, SortRelNode, FetchRelNode)):
        return infer_schema(node.input, ref_resolver)

    # --- Reshaping nodes ---
    if isinstance(node, ProjectRelNode):
        return _infer_project_schema(node, ref_resolver)

    if isinstance(node, AggregateRelNode):
        return _infer_aggregate_schema(node, ref_resolver)

    if isinstance(node, JoinRelNode):
        return _infer_join_schema(node, ref_resolver)

    if isinstance(node, SetRelNode):
        if node.inputs:
            return infer_schema(node.inputs[0], ref_resolver)
        return {}

    if isinstance(node, ExtensionRelNode):
        return infer_schema(node.input, ref_resolver)

    return {}


def _schema_from_source_data(data: Any) -> dict[str, Any]:
    """Extract column names from Python source data. Types are 'unknown'."""
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return {k: "unknown" for k in data[0].keys()}
    if isinstance(data, dict):
        return {k: "unknown" for k in data.keys()}
    return {}


def _infer_project_schema(node: Any, ref_resolver: Any) -> dict[str, Any]:
    """Infer schema for ProjectRelNode based on its operation type."""
    from mountainash.core.constants import ProjectOperation

    input_schema = infer_schema(node.input, ref_resolver)

    if node.operation == ProjectOperation.RENAME:
        mapping = node.rename_mapping or {}
        return {mapping.get(k, k): v for k, v in input_schema.items()}

    if node.operation == ProjectOperation.SELECT:
        result: dict[str, Any] = {}
        for expr in node.expressions:
            name = infer_expression_name(expr)
            if name and name in input_schema:
                result[name] = input_schema[name]
            elif name:
                result[name] = "unknown"
        return result

    if node.operation == ProjectOperation.WITH_COLUMNS:
        result = dict(input_schema)
        for expr in node.expressions:
            name = infer_expression_name(expr)
            if name:
                result[name] = input_schema.get(name, "unknown")
        return result

    if node.operation == ProjectOperation.DROP:
        drop_names = set()
        for expr in node.expressions:
            name = infer_expression_name(expr)
            if name:
                drop_names.add(name)
        return {k: v for k, v in input_schema.items() if k not in drop_names}

    return input_schema


def _infer_aggregate_schema(node: Any, ref_resolver: Any) -> dict[str, Any]:
    """Infer schema for AggregateRelNode: group keys + measure aliases."""
    input_schema = infer_schema(node.input, ref_resolver)
    result: dict[str, Any] = {}

    for key_expr in node.keys:
        name = infer_expression_name(key_expr)
        if name and name in input_schema:
            result[name] = input_schema[name]
        elif name:
            result[name] = "unknown"

    for measure_expr in node.measures:
        name = infer_expression_name(measure_expr)
        if name:
            result[name] = "unknown"

    return result


def _infer_join_schema(node: Any, ref_resolver: Any) -> dict[str, Any]:
    """Infer schema for JoinRelNode: left + right with suffix and key dedup."""
    from mountainash.core.constants import JoinType

    left_schema = infer_schema(node.left, ref_resolver)
    right_schema = infer_schema(node.right, ref_resolver)

    if node.join_type in (JoinType.SEMI, JoinType.ANTI):
        return left_schema

    result: dict[str, Any] = dict(left_schema)

    join_keys_right: set[str] = set()
    if node.on:
        join_keys_right = set(node.on)
    elif node.right_on:
        join_keys_right = set(node.right_on)

    suffix = node.suffix

    for col_name, col_type in right_schema.items():
        if col_name in join_keys_right and node.on:
            continue
        if col_name in result:
            result[col_name + suffix] = col_type
        else:
            result[col_name] = col_type

    return result
