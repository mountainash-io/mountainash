"""AST-level schema inference for relation node trees.

Walks the relation AST to extract {column_name: type} without compilation
or backend involvement. Types come from the source data (DataFrames,
DataResource schemas); column names come from the AST structure.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Optional

from mountainash.conform.contract import resolve_contract
from mountainash.conform.expressions import (
    _VALID_FIELDS_MATCH,
    PASSTHROUGH,
    UNDETERMINED,
    resolve_conform_output,
)
from mountainash.core.dtypes import MountainashDtype, TypeTarget, registry
from mountainash.core.dtypes.errors import UnknownDtypeError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_NAME,
)
from mountainash.expressions.core.output_names import resolve_output_names
from mountainash.relations.core.projection_names import require_projection_names
from mountainash.typespec.frictionless import typespec_from_frictionless
from mountainash.typespec.spec import FieldSpec
from mountainash.typespec.converters import resolve_field_canonical
from mountainash.typespec.universal_types import parse_universal


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

    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI

    if isinstance(expr_node, BaseExpressionAPI):
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


def _canon(
    native: Any, target: TypeTarget = TypeTarget.POLARS
) -> MountainashDtype | SchemaTypeStatus:
    """Map a native dtype to a canonical dtype or status.

    The canonical dtype is a ``MountainashDtype``, or a ``DecimalDtype`` for a native
    decimal column (precision and scale kept).

    ``None`` from the registry means the native is explicitly untyped
    (UNCONSTRAINED); an unrecognized native degrades to UNKNOWN rather than
    raising, since inference is best-effort.
    """
    try:
        canon = registry.from_native(native, target=target)
    except UnknownDtypeError:
        return SchemaTypeStatus.UNKNOWN
    return SchemaTypeStatus.UNCONSTRAINED if canon is None else canon


def _schema_from_dataframe(
    df: Any,
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Extract canonical schema from a native dataframe.

    Supports Polars DataFrame/LazyFrame, Ibis tables, pandas DataFrame, and
    raw Python data held unconverted by a ``ReadRelNode`` (a dict of columns
    or a list/tuple of row dicts) -- names only, dtype ``UNKNOWN``, because
    those inputs are converted to the execution backend only at compile time.
    Native dtypes are mapped through the dtype registry (per-backend target)
    to canonical ``MountainashDtype`` values, or a ``SchemaTypeStatus`` for
    typeless/unrecognized natives. Returns {} for unrecognized dataframe
    types (or a genuinely zero-column recognized dataframe). Never raises —
    introspection is always best-effort; an unmappable dtype degrades that
    one column to ``SchemaTypeStatus.UNKNOWN`` rather than aborting the
    whole extraction.
    """
    if hasattr(df, "collect_schema"):
        polars_schema = df.collect_schema()
        pairs = zip(polars_schema.names(), polars_schema.dtypes())
        return {name: _canon(dtype) for name, dtype in pairs}
    if hasattr(df, "schema") and not callable(df.schema):
        return {name: _canon(dtype) for name, dtype in dict(df.schema).items()}
    if hasattr(df, "schema") and callable(df.schema):
        # Ibis table: `.schema()` returns an ibis.Schema (dict-like of
        # name -> ibis dtype). Ibis dtype reprs ("string", "!int64") don't
        # match the Polars target's class-name keys ("String", "Int64"), so
        # this must resolve through TypeTarget.IBIS specifically — passing
        # the `_canon` default (POLARS) here degraded every Ibis column to
        # UNKNOWN regardless of its actual type (item 48 Task 7 fix).
        schema_obj = df.schema()
        if hasattr(schema_obj, "items"):
            return {
                name: _canon(dtype, target=TypeTarget.IBIS)
                for name, dtype in dict(schema_obj).items()
            }
    if hasattr(df, "dtypes"):
        # pandas DataFrame: `.dtypes` is a Series mapping column -> dtype.
        # Wrapped in a broad try/except (not just UnknownDtypeError) because
        # `dict(df.dtypes)` itself, or an exotic extension dtype's __str__,
        # could misbehave on inputs the pandas target module hasn't seen —
        # introspection must never raise, only degrade to UNKNOWN.
        result: dict[str, MountainashDtype | SchemaTypeStatus] = {}
        try:
            items = dict(df.dtypes).items()
        except Exception:
            return {}
        for name, dtype in items:
            try:
                result[name] = _canon(dtype, target=TypeTarget.PANDAS)
            except Exception:
                result[name] = SchemaTypeStatus.UNKNOWN
        return result
    if isinstance(df, dict):
        return {str(name): SchemaTypeStatus.UNKNOWN for name in df}
    if isinstance(df, (list, tuple)) and df and all(isinstance(row, dict) for row in df):
        names: dict[str, MountainashDtype | SchemaTypeStatus] = {}
        for row in df:
            for name in row:
                names.setdefault(str(name), SchemaTypeStatus.UNKNOWN)
        return names
    return {}
def _schema_from_table_schema(
    table_schema: dict,
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Extract field-aware canonical schema from a Frictionless table schema."""
    fields = table_schema.get("fields", [])
    if not fields:
        return {}
    result: dict[str, MountainashDtype | SchemaTypeStatus] = {}
    for raw_field in fields:
        name = raw_field.get("name")
        if not name or not raw_field.get("type"):
            if name:
                result[name] = SchemaTypeStatus.UNKNOWN
            continue
        try:
            field = FieldSpec(
                name=name,
                type=parse_universal(raw_field["type"]),
                format=raw_field.get("format", "default"),
                item_type=raw_field.get("itemType"),
                delimiter=raw_field.get("delimiter"),
            )
            canonical = resolve_field_canonical(field)
        except (KeyError, TypeError, ValueError):
            result[name] = SchemaTypeStatus.UNKNOWN
            continue
        result[name] = (
            SchemaTypeStatus.UNCONSTRAINED if canonical is None else canonical
        )
    return result


def _schema_from_typespec(
    spec: Any,
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Extract field-aware canonical schema from a resolved TypeSpec."""
    fields = getattr(spec, "fields", ())
    result: dict[str, MountainashDtype | SchemaTypeStatus] = {}
    for field in fields:
        try:
            canonical = resolve_field_canonical(field)
        except (KeyError, TypeError, ValueError):
            result[field.name] = SchemaTypeStatus.UNKNOWN
            continue
        result[field.name] = (
            SchemaTypeStatus.UNCONSTRAINED if canonical is None else canonical
        )
    return result


def infer_schema(
    node: Any,
    ref_resolver: Optional[
        Callable[[str], dict[str, MountainashDtype | SchemaTypeStatus]]
    ] = None,
    *,
    _drifts: Optional[list] = None,
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Walk a RelationNode tree and return {column_name: type} without compilation.

    Values are canonical ``MountainashDtype`` where inferable, or a
    ``SchemaTypeStatus`` (UNKNOWN / UNCONSTRAINED) where not.

    ``_drifts`` is a private accumulator (item 48 Task 9): when a caller
    passes a list, every ``ConformRelNode`` encountered during the walk
    appends its assessed :class:`~mountainash.conform.drift.ConformDrift`
    (if any) to it, in traversal order — this is how
    :func:`assess_drift` shares this exact walk without a second traversal.
    Public callers never pass this; it defaults to ``None`` (no collection).
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
        spec = node.resource.to_typespec()
        return _schema_from_typespec(spec) if spec is not None else {}

    if isinstance(node, SourceRelNode):
        return _schema_from_source_data(node.data)

    # --- Pass-through nodes ---
    if isinstance(node, (FilterRelNode, SortRelNode, FetchRelNode)):
        return infer_schema(node.input, ref_resolver, _drifts=_drifts)

    # --- Reshaping nodes ---
    if isinstance(node, ProjectRelNode):
        return _infer_project_schema(node, ref_resolver, _drifts=_drifts)

    if isinstance(node, AggregateRelNode):
        return _infer_aggregate_schema(node, ref_resolver, _drifts=_drifts)

    if isinstance(node, JoinRelNode):
        return _infer_join_schema(node, ref_resolver, _drifts=_drifts)

    if isinstance(node, SetRelNode):
        if node.inputs:
            return infer_schema(node.inputs[0], ref_resolver, _drifts=_drifts)
        return {}

    if isinstance(node, ConformRelNode):
        input_schema = infer_schema(node.input, ref_resolver, _drifts=_drifts)
        spec = node.spec
        if isinstance(spec, dict):
            spec = typespec_from_frictionless(spec)

        # Resolve the same contract layering apply_conform() honours
        # (TypeSpec.contract <- ConformRelNode.contract override) so build-time
        # inference/assessment agrees with execute-time policy (item 48 Task
        # 9 parity fix — previously this branch silently ignored both
        # layers). An invalid fields_match is left for resolve_conform_output
        # itself to raise its typed ConformError below (resolve_contract's
        # own bare-KeyError-on-unknown-preset behaviour is a pinned
        # invariant we must not trigger directly — see
        # UnifiedRelationVisitor.apply_conform's identical guard).
        fields_match = spec.fields_match
        resolved_contract = (
            resolve_contract(
                fields_match,
                spec_contract=getattr(spec, "contract", None),
                override=node.contract,
            )
            if fields_match in _VALID_FIELDS_MATCH
            else None
        )

        node_id = f"conform:{len(_drifts)}" if _drifts is not None else None
        contract = resolve_conform_output(
            spec,
            available_columns=list(input_schema.keys()),
            actual_dtypes=input_schema,
            contract=resolved_contract,
            node_identity=(node_id, None, getattr(spec, "name", None)),
            raise_on_freeze=False,
            apply_value_transforms=node.apply_value_transforms,
        )
        if _drifts is not None and contract.drift is not None:
            _drifts.append(contract.drift)
        if not node.apply_value_transforms:
            emitted = {
                em.field.name: input_schema.get(em.source_name, SchemaTypeStatus.UNKNOWN)
                if em.type_action != "null_fill"
                else _declared_dtype_for_infer(em, input_schema)
                for em in contract.emitted
            }
        else:
            emitted = {
                em.field.name: _declared_dtype_for_infer(em, input_schema)
                for em in contract.emitted
            }
        if contract.keeps_unmapped:
            result = dict(input_schema)
            for source in contract.renamed_sources:
                result.pop(source, None)
            result.update(emitted)
            return result
        return emitted

    if isinstance(node, ExtensionRelNode):
        return infer_schema(node.input, ref_resolver, _drifts=_drifts)

    return {}


def assess_drift(
    node: Any,
    ref_resolver: Optional[
        Callable[[str], dict[str, MountainashDtype | SchemaTypeStatus]]
    ] = None,
) -> list:
    """Schema-only pre-flight: assess drift at every ``ConformRelNode`` in the plan.

    Shares :func:`infer_schema`'s exact AST walk (via the private ``_drifts``
    accumulator) so every ``ConformRelNode`` anywhere in the tree — nested
    under filters, sorts, projects, aggregates, joins, sets, extensions — is
    visited in the same depth-first order the execute-time visitor uses for
    ``UnifiedRelationVisitor.drift_reports`` (children before the node that
    consumes them; left before right for joins).

    Drift assembly runs with policy enforcement (raising/filtering) disabled
    (``raise_on_freeze=False``) — a ``freeze``-configured node is still
    reported here, never raised. This function never raises
    ``SchemaDriftError``, never compiles, and never touches a backend.

    Returns:
        A list of :class:`~mountainash.conform.drift.ConformDrift`, one per
        conform node with assessable evidence, in traversal order. A node
        with no available columns and no actual-dtype evidence contributes
        nothing (honest non-assessment).
    """
    drifts: list = []
    infer_schema(node, ref_resolver, _drifts=drifts)
    return drifts


def _declared_dtype_for_infer(
    em: Any,
    input_schema: dict[str, MountainashDtype | SchemaTypeStatus],
) -> MountainashDtype | SchemaTypeStatus:
    """Resolve an EmittedField's declared_type against an upstream schema.

    - ``type_action == "evolve"`` (item 48 Task 9, R2) → the output keeps the
      source's actual type: ``em.effective_type`` when the data_type drift
      loop resolved a concrete dtype, else ``UNKNOWN`` (evidence was
      unknowable — honest non-assessment, not a guess). This check runs
      first because "evolve" overrides whatever ``declared_type`` would
      otherwise resolve to.
    - Concrete :class:`MountainashDtype` → returned as-is.
    - ``PASSTHROUGH`` → look up ``em.source_name`` in ``input_schema`` (UNKNOWN
      if absent — e.g. dotted struct child where the root is present but the
      child isn't represented in the input schema).
    - ``UNDETERMINED`` → ``SchemaTypeStatus.UNKNOWN`` (cannot be predicted
      pre-compile; e.g. ANY + null_fill, dotted ANY, non-Polars categorical).
    """
    if em.type_action == "evolve":
        return (
            em.effective_type
            if em.effective_type is not None
            else SchemaTypeStatus.UNKNOWN
        )
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
    node: Any, ref_resolver: Any, *, _drifts: Optional[list] = None
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Infer schema for ProjectRelNode based on its operation type."""
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_SUBSTRAIT_REL,
    )

    input_schema = infer_schema(node.input, ref_resolver, _drifts=_drifts)

    if node.operation == RKEY_SUBSTRAIT_REL.PROJECT_RENAME:
        mapping = node.rename_mapping or {}
        return {mapping.get(k, k): v for k, v in input_schema.items()}

    if node.operation in {RKEY_SUBSTRAIT_REL.PROJECT_SELECT, RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS}:
        names = require_projection_names(
            node.expressions, operation=node.operation, input_names=tuple(input_schema)
        )
        result = dict(input_schema) if node.operation == RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS else {}
        for name in names:
            result[name] = input_schema.get(name, SchemaTypeStatus.UNKNOWN)
        return result

    if node.operation == RKEY_SUBSTRAIT_REL.PROJECT_DROP:
        drop_names = set()
        for expr in node.expressions:
            name = infer_expression_name(expr)
            if name:
                drop_names.add(name)
        return {k: v for k, v in input_schema.items() if k not in drop_names}

    return input_schema


def _aggregate_source_names(data: Any) -> tuple[str, ...] | None:
    """Cheap source metadata, retaining unavailable versus known-empty names."""
    if isinstance(data, dict):
        return tuple(str(name) for name in data)
    if isinstance(data, (list, tuple)) and data and all(isinstance(row, dict) for row in data):
        return tuple(dict.fromkeys(str(name) for row in data for name in row))
    try:
        if hasattr(data, "collect_schema"):
            return tuple(data.collect_schema().names())
        if hasattr(data, "schema"):
            schema = data.schema() if callable(data.schema) else data.schema
            if hasattr(schema, "items"):
                return tuple(schema)
        if hasattr(data, "dtypes"):
            return tuple(dict(data.dtypes))
    except Exception:
        # Metadata extraction failure is unavailable evidence, never zero columns.
        return None
    return None


def _aggregate_resource_names(node: Any) -> tuple[str, ...] | None:
    """Closed effective conform policy proves the successful reader's output."""
    from mountainash.typespec.spec import TypeSpec

    if not node.apply_schema_conform:
        return None
    spec = node.resource.table_schema
    if isinstance(spec, dict):
        spec = typespec_from_frictionless(spec)
    if not isinstance(spec, TypeSpec) or spec.fields_match not in _VALID_FIELDS_MATCH:
        return None  # In particular, do not fetch referenced schemas.
    contract = resolve_contract(spec.fields_match, spec_contract=spec.contract)
    if (
        contract.mapping != "by_name"
        or contract.extra_columns == "evolve"
        or contract.missing_columns == "skip"
    ):
        return None
    # Every declared field must exist or be null-filled; extras cannot survive.
    # The conform projection emits fields in declaration order on every backend.
    return tuple(field.name for field in spec.fields)


def _aggregate_input_names(node: Any) -> tuple[str, ...] | None:
    """Prove aggregate input names independently of best-effort dtype inference."""
    from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT as PF
    from mountainash.relations.core.relation_nodes import (
        AggregateRelNode, FetchRelNode, FilterRelNode, ProjectRelNode, ReadRelNode, SortRelNode,
    )
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode, SourceRelNode
    from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL as RS

    if isinstance(node, ReadRelNode):
        return _aggregate_source_names(node.dataframe)
    if isinstance(node, SourceRelNode):
        if node.detected_format in {PF.PYDICT, PF.PYLIST, PF.SERIES_DICT}:
            return _aggregate_source_names(node.data)
        return None  # Indexed dictionaries/tuples are rows, not column mappings.
    if isinstance(node, ResourceReadRelNode):
        return _aggregate_resource_names(node)
    if isinstance(node, (FilterRelNode, SortRelNode, FetchRelNode)):
        return _aggregate_input_names(node.input)
    if isinstance(node, AggregateRelNode):
        names = _aggregate_input_names(node.input)
        if not node.measures:
            # Keyless DISTINCT preserves columns. Subset DISTINCT currently
            # retains non-key columns on Polars/Narwhals but drops them on Ibis.
            return None if node.keys else names
        return require_projection_names(
            [*node.keys, *node.measures], operation=node.operation_key, input_names=names,
        )
    if isinstance(node, ProjectRelNode):
        names = _aggregate_input_names(node.input)
        if node.operation == RS.PROJECT_SELECT:
            return require_projection_names(node.expressions, operation=node.operation, input_names=names)
        if names is None:
            return None
        if node.operation == RS.PROJECT_WITH_COLUMNS:
            added = require_projection_names(node.expressions, operation=node.operation, input_names=names)
            return tuple(dict.fromkeys((*names, *added)))
        if node.operation == RS.PROJECT_RENAME:
            mapping = node.rename_mapping or {}
            return tuple(mapping.get(name, name) for name in names)
        if node.operation == RS.PROJECT_DROP:
            dropped = require_projection_names(node.expressions, operation=node.operation, input_names=names)
            return tuple(name for name in names if name not in dropped)
    # Ref dtype resolvers do not certify completeness; joins/sets/conform/
    # extensions need their own proof.
    return None


def _aggregate_key_source(expression: Any) -> str | None:
    """Source of a plain field under name-only wrappers, not value transforms."""
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode

    if isinstance(expression, BaseExpressionAPI):
        expression = expression._node
    if isinstance(expression, str):
        return expression
    if isinstance(expression, FieldReferenceNode):
        return expression.field if expression.unknown_values is None else None
    if isinstance(expression, ScalarFunctionNode) and expression.function_key in {
        FKEY_MOUNTAINASH_NAME.ALIAS, FKEY_MOUNTAINASH_NAME.PREFIX, FKEY_MOUNTAINASH_NAME.SUFFIX,
        FKEY_MOUNTAINASH_NAME.NAME_TO_UPPER, FKEY_MOUNTAINASH_NAME.NAME_TO_LOWER,
    }:
        return _aggregate_key_source(expression.arguments[0])
    return None


def _infer_aggregate_schema(
    node: Any, ref_resolver: Any, *, _drifts: Optional[list] = None
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Resolve complete aggregate names and retain only proven key source types."""
    input_schema = infer_schema(node.input, ref_resolver, _drifts=_drifts)
    if not node.measures:
        # Preserve the existing key-only DISTINCT schema behavior.
        result = {}
        for key in node.keys:
            name = infer_expression_name(key)
            if name:
                result[name] = input_schema.get(name, SchemaTypeStatus.UNKNOWN)
        return result

    input_names = _aggregate_input_names(node.input)
    names = require_projection_names(
        [*node.keys, *node.measures], operation=node.operation_key, input_names=input_names,
    )
    result = dict.fromkeys(names, SchemaTypeStatus.UNKNOWN)
    for key in node.keys:
        output = resolve_output_names(key, input_names=input_names)
        source = _aggregate_key_source(key)
        if output.scalar_name is not None and source is not None:
            result[output.scalar_name] = input_schema.get(source, SchemaTypeStatus.UNKNOWN)

    return result


def _infer_join_schema(
    node: Any, ref_resolver: Any, *, _drifts: Optional[list] = None
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Infer schema for JoinRelNode; keyed joins follow ``join_layout``."""
    from mountainash.core.constants import JoinType

    left_schema = infer_schema(node.left, ref_resolver, _drifts=_drifts)
    right_schema = infer_schema(node.right, ref_resolver, _drifts=_drifts)

    if node.join_type in (JoinType.SEMI, JoinType.ANTI):
        return left_schema

    from mountainash.relations.core.join_layout import keyed_layout_applies, layout_for_node

    if keyed_layout_applies(node):
        layout = layout_for_node(node, list(left_schema), list(right_schema))
        keyed: dict[str, MountainashDtype | SchemaTypeStatus] = dict(left_schema)
        for name, dtype in right_schema.items():
            keyed[layout.right_rename.get(name, name)] = dtype
        for name in layout.drop:
            keyed.pop(name, None)
        # A merged key holds coalesce(left, right); like projection inference
        # of that expression, its dtype is only known when both sides agree.
        original = {final: name for name, final in layout.right_rename.items()}
        for left_key, right_key in layout.merge:
            right_dtype = right_schema.get(original.get(right_key, right_key))
            if keyed.get(left_key) != right_dtype:
                keyed[left_key] = SchemaTypeStatus.UNKNOWN
        return keyed

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
