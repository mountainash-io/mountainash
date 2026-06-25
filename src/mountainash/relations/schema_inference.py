"""AST-level schema inference for relation node trees.

Walks the relation AST to extract {column_name: type} without compilation
or backend involvement. Types come from the source data (DataFrames,
DataResource schemas); column names come from the AST structure.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Optional

from mountainash.conform.expressions import (
    PASSTHROUGH,
    UNDETERMINED,
    resolve_conform_output,
)
from mountainash.core.dtypes import MountainashDtype, TypeTarget, registry
from mountainash.core.dtypes.errors import UnknownDtypeError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_NAME,
)
from mountainash.typespec.frictionless import typespec_from_frictionless
from mountainash.typespec.universal_types import parse_universal, to_canonical


class SchemaTypeStatus(Enum):
    """Non-type states in an inferred schema (replaces the 'unknown' string)."""

    UNKNOWN = "unknown"            # not inferable from this plan node
    UNCONSTRAINED = "unconstrained"  # source declared ANY (explicitly typeless)


def infer_expression_name(expr_node: Any) -> Optional[str]:
    """Extract the output column name from an expression node tree.

    Returns the alias name if the expression is wrapped in an ALIAS node,
    the field name if it's a bare FieldReferenceNode, or None if the name
    cannot be determined. Also handles plain strings (from select("a"))
    and API wrapper objects (from with_columns(expr)).
    """
    if isinstance(expr_node, str):
        return expr_node

    if hasattr(expr_node, "_node"):
        return infer_expression_name(expr_node._node)

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


def _canon(native: Any) -> MountainashDtype | SchemaTypeStatus:
    """Map a native (polars) dtype to a canonical MountainashDtype or status.

    ``None`` from the registry means the native is explicitly untyped
    (UNCONSTRAINED); an unrecognized native degrades to UNKNOWN rather than
    raising, since inference is best-effort.
    """
    try:
        canon = registry.from_native(native, target=TypeTarget.POLARS)
    except UnknownDtypeError:
        return SchemaTypeStatus.UNKNOWN
    return SchemaTypeStatus.UNCONSTRAINED if canon is None else canon


def _schema_from_dataframe(
    df: Any,
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Extract canonical schema from a native dataframe.

    Supports Polars DataFrame/LazyFrame. Native dtypes are mapped through the
    dtype registry (POLARS target) to canonical ``MountainashDtype`` values, or
    a ``SchemaTypeStatus`` for typeless/unrecognized natives. Returns {} for
    unrecognized dataframe types. Isolated for future refinement (narwhals,
    pandas, etc.).
    """
    if hasattr(df, "collect_schema"):
        polars_schema = df.collect_schema()
        pairs = zip(polars_schema.names(), polars_schema.dtypes())
        return {name: _canon(dtype) for name, dtype in pairs}
    if hasattr(df, "schema") and not callable(df.schema):
        return {name: _canon(dtype) for name, dtype in dict(df.schema).items()}
    if hasattr(df, "schema") and callable(df.schema):
        schema_obj = df.schema()
        if hasattr(schema_obj, "items"):
            return {
                name: _canon(dtype) for name, dtype in dict(schema_obj).items()
            }
    return {}


def _schema_from_table_schema(
    table_schema: dict,
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Extract canonical schema from a Frictionless table_schema dict.

    Each field's Frictionless type string is parsed and converted to a
    canonical ``MountainashDtype``. A missing/empty type or an unrecognized
    string yields ``SchemaTypeStatus.UNKNOWN``; an explicitly typeless ``any``
    field yields ``SchemaTypeStatus.UNCONSTRAINED``. Isolated for future
    refinement.
    """
    fields = table_schema.get("fields", [])
    if not fields:
        return {}
    result: dict[str, MountainashDtype | SchemaTypeStatus] = {}
    for f in fields:
        type_str = f.get("type")
        if not type_str:
            result[f["name"]] = SchemaTypeStatus.UNKNOWN
            continue
        try:
            canon = to_canonical(parse_universal(type_str))
        except UnknownDtypeError:
            result[f["name"]] = SchemaTypeStatus.UNKNOWN
            continue
        result[f["name"]] = (
            SchemaTypeStatus.UNCONSTRAINED if canon is None else canon
        )
    return result


def infer_schema(
    node: Any,
    ref_resolver: Optional[
        Callable[[str], dict[str, MountainashDtype | SchemaTypeStatus]]
    ] = None,
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Walk a RelationNode tree and return {column_name: type} without compilation.

    Values are canonical ``MountainashDtype`` where inferable, or a
    ``SchemaTypeStatus`` (UNKNOWN / UNCONSTRAINED) where not.
    """
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
        ConformRelNode,
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

    if isinstance(node, ConformRelNode):
        input_schema = infer_schema(node.input, ref_resolver)
        spec = node.spec
        if isinstance(spec, dict):
            spec = typespec_from_frictionless(spec)
        contract = resolve_conform_output(
            spec, available_columns=list(input_schema.keys())
        )
        emitted = {
            em.field.name: _declared_dtype_for_infer(em, input_schema)
            for em in contract.emitted
        }
        if contract.keeps_unmapped:  # open → with_columns semantics
            result = dict(input_schema)
            for s in contract.renamed_sources:
                result.pop(s, None)
            result.update(emitted)
            return result
        return emitted  # select modes → projection only

    if isinstance(node, ExtensionRelNode):
        return infer_schema(node.input, ref_resolver)

    return {}


def _declared_dtype_for_infer(
    em: Any,
    input_schema: dict[str, MountainashDtype | SchemaTypeStatus],
) -> MountainashDtype | SchemaTypeStatus:
    """Resolve an EmittedField's declared_type against an upstream schema.

    - Concrete :class:`MountainashDtype` → returned as-is.
    - ``PASSTHROUGH`` → look up ``em.source_name`` in ``input_schema`` (UNKNOWN
      if absent — e.g. dotted struct child where the root is present but the
      child isn't represented in the input schema).
    - ``UNDETERMINED`` → ``SchemaTypeStatus.UNKNOWN`` (cannot be predicted
      pre-compile; e.g. ANY + null_fill, dotted ANY, non-Polars categorical).
    """
    dt = em.declared_type
    if dt is PASSTHROUGH:
        return input_schema.get(em.source_name, SchemaTypeStatus.UNKNOWN)
    if dt is UNDETERMINED:
        return SchemaTypeStatus.UNKNOWN
    return dt


def _schema_from_source_data(
    data: Any,
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Extract column names and infer types from Python source data.

    Delegates to _schema_from_dataframe via pl.DataFrame(data, strict=False) so
    inference matches the runtime ingress path exactly. strict=False matches
    pydata/ingress paths that also use strict=False.

    Falls back to names-only (UNKNOWN) if DataFrame construction fails — preserving
    old behaviour for genuinely-unconstructable data.
    """
    if isinstance(data, list) and data and isinstance(data[0], dict):
        keys = list(data[0].keys())
        import polars as pl
        try:
            frame = pl.DataFrame(data, strict=False)
        except Exception:
            return {k: SchemaTypeStatus.UNKNOWN for k in keys}
        return _schema_from_dataframe(frame)
    if isinstance(data, dict):
        keys = list(data.keys())
        import polars as pl
        try:
            frame = pl.DataFrame(data, strict=False)
        except Exception:
            return {k: SchemaTypeStatus.UNKNOWN for k in keys}
        return _schema_from_dataframe(frame)
    return {}


def _infer_project_schema(
    node: Any, ref_resolver: Any
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Infer schema for ProjectRelNode based on its operation type."""
    from mountainash.core.constants import ProjectOperation

    input_schema = infer_schema(node.input, ref_resolver)

    if node.operation == ProjectOperation.RENAME:
        mapping = node.rename_mapping or {}
        return {mapping.get(k, k): v for k, v in input_schema.items()}

    if node.operation == ProjectOperation.SELECT:
        result: dict[str, MountainashDtype | SchemaTypeStatus] = {}
        for expr in node.expressions:
            name = infer_expression_name(expr)
            if name and name in input_schema:
                result[name] = input_schema[name]
            elif name:
                result[name] = SchemaTypeStatus.UNKNOWN
        return result

    if node.operation == ProjectOperation.WITH_COLUMNS:
        result = dict(input_schema)
        for expr in node.expressions:
            name = infer_expression_name(expr)
            if name:
                result[name] = input_schema.get(name, SchemaTypeStatus.UNKNOWN)
        return result

    if node.operation == ProjectOperation.DROP:
        drop_names = set()
        for expr in node.expressions:
            name = infer_expression_name(expr)
            if name:
                drop_names.add(name)
        return {k: v for k, v in input_schema.items() if k not in drop_names}

    return input_schema


def _infer_aggregate_schema(
    node: Any, ref_resolver: Any
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Infer schema for AggregateRelNode: group keys + measure aliases."""
    input_schema = infer_schema(node.input, ref_resolver)
    result: dict[str, MountainashDtype | SchemaTypeStatus] = {}

    for key_expr in node.keys:
        name = infer_expression_name(key_expr)
        if name and name in input_schema:
            result[name] = input_schema[name]
        elif name:
            result[name] = SchemaTypeStatus.UNKNOWN

    for measure_expr in node.measures:
        name = infer_expression_name(measure_expr)
        if name:
            result[name] = SchemaTypeStatus.UNKNOWN

    return result


def _infer_join_schema(
    node: Any, ref_resolver: Any
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Infer schema for JoinRelNode: left + right with suffix and key dedup."""
    from mountainash.core.constants import JoinType

    left_schema = infer_schema(node.left, ref_resolver)
    right_schema = infer_schema(node.right, ref_resolver)

    if node.join_type in (JoinType.SEMI, JoinType.ANTI):
        return left_schema

    result: dict[str, MountainashDtype | SchemaTypeStatus] = dict(left_schema)

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
