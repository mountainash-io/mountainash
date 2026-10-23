"""AST-level schema inference for relation node trees.

Walks the relation AST to extract {column_name: type} without compilation
or execution. Types come from source schemas and cheap native-route metadata;
column names come from the AST structure.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any, Callable, Optional

from mountainash.conform.contract import resolve_contract
from mountainash.conform.expressions import (
    _VALID_FIELDS_MATCH,
    PASSTHROUGH,
    UNDETERMINED,
    resolve_conform_output,
)
from mountainash.core.dtypes import MountainashDtype, TypeTarget, registry
from mountainash.core.dtypes.canonical import (
    ArrayDtype,
    DecimalDtype,
    DurationDtype,
    ListDtype,
    NativeDtype,
    SchemaTypeStatus,
    StructDtype,
    TimeDtype,
    TimestampDtype,
)
from mountainash.core.dtypes.errors import UnknownDtypeError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_NAME,
)
from mountainash.expressions.core.output_names import resolve_output_names
from mountainash.relations.core.projection_names import require_projection_names
from mountainash.typespec.frictionless import table_schema_from_frictionless
from mountainash.typespec.converters import resolve_field_canonical


_DetailedDtype = (
    MountainashDtype
    | DecimalDtype
    | NativeDtype
    | TimestampDtype
    | TimeDtype
    | DurationDtype
    | ListDtype
    | ArrayDtype
    | StructDtype
)

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
) -> _DetailedDtype | SchemaTypeStatus:
    """Map native metadata to a detailed canonical dtype or inference status.

    ``None`` from the registry means the native is explicitly untyped
    (UNCONSTRAINED); an unrecognized native degrades to UNKNOWN rather than
    raising. Known native-only types remain NativeDtype values.
    """
    try:
        canon = registry.from_native(native, target=target)
    except UnknownDtypeError:
        return SchemaTypeStatus.UNKNOWN
    return SchemaTypeStatus.UNCONSTRAINED if canon is None else canon


def _schema_from_dataframe(df: Any) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Logical output types of a native table carrier, from its schema adapter.

    The carrier's native schema adapter (selected by central carrier recognition)
    supplies the evidence; nothing here inspects a physical engine or executes.
    Raw Python data held unconverted by a ``ReadRelNode`` retains only output
    names and UNKNOWN dtype states until compilation supplies a carrier, and an
    unsupported object has no schema.
    """
    from mountainash.core.types import detect_schema_carrier
    from mountainash.typespec.source_shape import extract_source_shapes, shape_type_evidence

    if detect_schema_carrier(df) is not None:
        return {name: shape_type_evidence(shape) for name, shape in extract_source_shapes(df).items()}
    if isinstance(df, dict):
        return {str(name): SchemaTypeStatus.UNKNOWN for name in df}
    if isinstance(df, (list, tuple)) and df and all(isinstance(row, dict) for row in df):
        names: dict[str, _DetailedDtype | SchemaTypeStatus] = {}
        for row in df:
            for name in row:
                names.setdefault(str(name), SchemaTypeStatus.UNKNOWN)
        return names
    return {}


def _schema_from_table_schema(
    table_schema: dict,
) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Extract field-aware canonical schema from a Frictionless table schema."""
    result: dict[str, _DetailedDtype | SchemaTypeStatus] = {}
    for raw_field in table_schema.get("fields", []):
        name = raw_field.get("name")
        if not name:
            continue
        try:
            field = table_schema_from_frictionless({"fields": [raw_field]}).fields[name]
            canonical = resolve_field_canonical(field)
        except (KeyError, TypeError, ValueError):
            result[name] = SchemaTypeStatus.UNKNOWN
            continue
        result[name] = (
            SchemaTypeStatus.UNKNOWN if field.backend_type
            else SchemaTypeStatus.UNKNOWN
            if canonical is SchemaTypeStatus.UNCONSTRAINED and not raw_field.get("type")
            else canonical
        )
    return result


def _schema_from_declaration(
    spec: Any,
) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Extract field-aware canonical schema from a resolved TableSchema."""
    fields = getattr(spec, "fields", {})
    result: dict[str, _DetailedDtype | SchemaTypeStatus] = {}
    for name, field in fields.items():
        try:
            canonical = resolve_field_canonical(field)
        except (KeyError, TypeError, ValueError):
            result[name] = SchemaTypeStatus.UNKNOWN
            continue
        result[name] = (
            SchemaTypeStatus.UNKNOWN if field.backend_type
            else SchemaTypeStatus.UNCONSTRAINED if canonical is None else canonical
        )
    return result


def infer_schema(
    node: Any,
    ref_resolver: Optional[
        Callable[[str], dict[str, _DetailedDtype | SchemaTypeStatus]]
    ] = None,
    *,
    identity_resolver: Optional[Callable[[str], Any]] = None,
    _drifts: Optional[list] = None,
) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Walk a RelationNode tree and return {column_name: type} without compilation.

    Values are canonical ``MountainashDtype`` where inferable, or a
    ``SchemaTypeStatus`` (UNKNOWN / UNCONSTRAINED) where not.

    ``identity_resolver`` optionally supplies referenced nodes for native
    metadata; ``ref_resolver`` continues to supply their inferred schemas.

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
        spec = node.resource.to_table_schema()
        return _schema_from_declaration(spec) if spec is not None else {}

    if isinstance(node, SourceRelNode):
        return _schema_from_source_data(node.data)

    # --- Pass-through nodes ---
    if isinstance(node, (FilterRelNode, SortRelNode, FetchRelNode)):
        return infer_schema(node.input, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)

    # --- Reshaping nodes ---
    if isinstance(node, ProjectRelNode):
        return _infer_project_schema(node, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)

    if isinstance(node, AggregateRelNode):
        return _infer_aggregate_schema(node, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)

    if isinstance(node, JoinRelNode):
        return _infer_join_schema(node, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)

    if isinstance(node, SetRelNode):
        if node.inputs:
            return infer_schema(node.inputs[0], ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)
        return {}

    if isinstance(node, ConformRelNode):
        input_schema = infer_schema(node.input, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)
        spec = node.spec
        if isinstance(spec, dict):
            spec = table_schema_from_frictionless(spec)

        # Resolve the same contract layering apply_conform() honours
        # (TableSchema.contract <- ConformRelNode.contract override) so build-time
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
        from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
        from mountainash.relations.core.errors import UnresolvedExecutionLocationError
        from mountainash.relations.dag.errors import RelationDAGRequired
        from mountainash.typespec.converters import _execution_type_target
        from mountainash.typespec.source_shape import extract_source_shapes
        try:
            location = LocationResolver(IdentityTokens(), identity_resolver=identity_resolver).resolve(node)
            type_target = _execution_type_target(location.family)
        except UnresolvedExecutionLocationError:
            raise
        except (RelationDAGRequired, ValueError):
            type_target = None
        actual_shapes = (
            extract_source_shapes(node.input.dataframe, target=type_target)
            if isinstance(node.input, ReadRelNode)
            and type_target is not None
            and not isinstance(node.input.dataframe, (list, tuple, dict)) else None
        )
        contract = resolve_conform_output(
            spec,
            available_columns=list(input_schema.keys()),
            actual_dtypes=input_schema,
            actual_shapes=actual_shapes,
            type_target=type_target,
            contract=resolved_contract,
            node_identity=(node_id, None, getattr(spec, "name", None)),
            raise_on_freeze=False,
            apply_value_transforms=node.apply_value_transforms,
        )
        if _drifts is not None and contract.drift is not None:
            _drifts.append(contract.drift)
        return contract.output_schema

    if isinstance(node, ExtensionRelNode):
        from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

        input_schema = infer_schema(node.input, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)
        if node.operation == RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX:
            return _infer_row_index_schema(node, input_schema, identity_resolver)
        return input_schema

    return {}


def _infer_row_index_schema(
    node: Any, input_schema: dict, identity_resolver: Any,
) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Describe native ordinal metadata without requiring an executable source."""
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.lazy_imports import import_polars
    from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
    from mountainash.relations.dag.errors import RelationDAGRequired

    name = node.options.get("name", "index")
    dtype = SchemaTypeStatus.UNKNOWN
    prepend = False
    try:
        location = LocationResolver(
            IdentityTokens(), identity_resolver=identity_resolver,
        ).resolve(node)
    except RelationDAGRequired:
        # A schema-only ref is useful to inspect before its source is bound.
        location = None
    if location is not None:
        if location.family is CONST_BACKEND.POLARS or location.dialect == "narwhals-polars":
            dtype = _canon(import_polars().get_index_type())
            prepend = True
        elif location.family is CONST_BACKEND.IBIS:
            dtype = MountainashDtype.I64
        elif location.family in {CONST_BACKEND.PANDAS, CONST_BACKEND.PYARROW} or location.dialect in {
            "narwhals-pandas", "narwhals-pyarrow",
        }:
            dtype = MountainashDtype.I64
            prepend = True
    # For unknown routes this position is descriptive, not a native-layout promise.
    result = {name: dtype} if prepend else {}
    result.update(input_schema)
    result[name] = dtype
    return result


def assess_drift(
    node: Any,
    ref_resolver: Optional[
        Callable[[str], dict[str, _DetailedDtype | SchemaTypeStatus]]
    ] = None,
    *,
    identity_resolver: Optional[Callable[[str], Any]] = None,
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
    infer_schema(node, ref_resolver, identity_resolver=identity_resolver, _drifts=drifts)
    return drifts




def _schema_from_source_data(
    data: Any,
) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Extract column names and infer types from Python source data.

    Dataclass instances and homogeneous lists use declarations without reading
    row values. Mixed-class lists do not have a complete-schema guarantee.
    Dictionary inputs use pl.DataFrame(data, strict=False), matching ingress,
    with names-only (UNKNOWN) fallback if construction fails.
    """
    instance = data[0] if isinstance(data, list) and data else data
    if is_dataclass(instance) and not isinstance(instance, type):
        from mountainash.typespec.extraction import extract_from_dataclass
        from mountainash.typespec.universal_types import UniversalType as U

        model_type = type(instance)
        schema = {field.name: SchemaTypeStatus.UNKNOWN for field in fields(model_type)}
        try:
            spec = extract_from_dataclass(model_type)
        except Exception:
            # Hint resolution is best-effort metadata; names remain usable.
            return schema
        declared = _schema_from_declaration(spec)
        # Match the flat model evidence honored by PyData ingress. ANY retains
        # the existing unconstrained status, not a fabricated concrete dtype.
        scalar_types = {
            U.STRING, U.INTEGER, U.NUMBER, U.BOOLEAN, U.DATE, U.DATETIME,
            U.TIME, U.DURATION, U.YEAR, U.YEARMONTH, U.ANY,
        }
        for name, field in spec.fields.items():
            if name in schema and field.type in scalar_types:
                schema[name] = declared[name]
        return schema
    if isinstance(data, list) and data and isinstance(data[0], dict):
        keys = list(data[0].keys())
        from mountainash.pydata.ingress.pydata_ingress import schema_literal_ingress_safe
        if not schema_literal_ingress_safe(data):
            return {k: SchemaTypeStatus.UNKNOWN for k in keys}
        import polars as pl
        try:
            frame = pl.DataFrame(data, strict=False)
        except Exception:
            return {k: SchemaTypeStatus.UNKNOWN for k in keys}
        return _schema_from_dataframe(frame)
    if isinstance(data, dict):
        keys = list(data.keys())
        from mountainash.pydata.ingress.pydata_ingress import schema_literal_ingress_safe
        if not schema_literal_ingress_safe(data):
            return {k: SchemaTypeStatus.UNKNOWN for k in keys}
        import polars as pl
        try:
            frame = pl.DataFrame(data, strict=False)
        except Exception:
            return {k: SchemaTypeStatus.UNKNOWN for k in keys}
        return _schema_from_dataframe(frame)
    return {}


def _infer_project_schema(
    node: Any, ref_resolver: Any, *, identity_resolver: Any = None, _drifts: Optional[list] = None
) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Infer schema for ProjectRelNode based on its operation type."""
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_SUBSTRAIT_REL,
    )

    input_schema = infer_schema(node.input, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)

    if node.operation == RKEY_SUBSTRAIT_REL.PROJECT_RENAME:
        mapping = node.rename_mapping or {}
        return {mapping.get(k, k): v for k, v in input_schema.items()}

    if node.operation in {RKEY_SUBSTRAIT_REL.PROJECT_SELECT, RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS}:
        input_names = tuple(input_schema)
        names = require_projection_names(
            node.expressions, operation=node.operation, input_names=input_names
        )
        result = dict(input_schema) if node.operation == RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS else {}
        for name in names:
            result[name] = SchemaTypeStatus.UNKNOWN
        for expression in node.expressions:
            # Aggregate keys and projections share the same field-identity rule.
            source = _aggregate_key_source(expression)
            if source is None:
                continue
            source_names = resolve_output_names(source, input_names=input_names).names
            output_names = resolve_output_names(expression, input_names=input_names).names
            if source_names is not None and output_names is not None and len(source_names) == len(output_names):
                for output_name, source_name in zip(output_names, source_names):
                    result[output_name] = input_schema.get(source_name, SchemaTypeStatus.UNKNOWN)
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
    from mountainash.typespec.spec import TableSchema

    if not node.apply_schema_conform:
        return None
    spec = node.resource.table_schema
    if isinstance(spec, dict):
        spec = table_schema_from_frictionless(spec)
    if not isinstance(spec, TableSchema) or spec.fields_match not in _VALID_FIELDS_MATCH:
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
    return tuple(spec.fields)


def _aggregate_input_names(node: Any) -> tuple[str, ...] | None:
    """Prove aggregate input names independently of best-effort dtype inference."""
    from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT as PF
    from mountainash.relations.core.relation_nodes import (
        AggregateRelNode, FetchRelNode, FilterRelNode, JoinRelNode, ProjectRelNode, ReadRelNode, SortRelNode,
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
    if isinstance(node, JoinRelNode):
        from mountainash.relations.core.join_layout import keyed_layout_applies, layout_for_node
        left = _aggregate_input_names(node.left)
        right = _aggregate_input_names(node.right)
        if left is not None and right is not None and keyed_layout_applies(node):
            layout = layout_for_node(node, list(left), list(right))
            right_output = (layout.right_rename.get(name, name) for name in right)
            return (*left, *(name for name in right_output if name not in layout.drop))
        return None
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
    node: Any, ref_resolver: Any, *, identity_resolver: Any = None, _drifts: Optional[list] = None
) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Resolve complete aggregate names and retain only proven key source types."""
    input_schema = infer_schema(node.input, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)
    if not node.measures:
        if not node.keys:
            return input_schema  # Whole-row DISTINCT preserves every input field.
        # Preserve the existing key-only schema behavior for keyed DISTINCT.
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
    node: Any, ref_resolver: Any, *, identity_resolver: Any = None, _drifts: Optional[list] = None
) -> dict[str, _DetailedDtype | SchemaTypeStatus]:
    """Infer schema for JoinRelNode; keyed joins follow ``join_layout``."""
    from mountainash.core.constants import JoinType

    left_schema = infer_schema(node.left, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)
    right_schema = infer_schema(node.right, ref_resolver, identity_resolver=identity_resolver, _drifts=_drifts)

    if node.join_type in (JoinType.SEMI, JoinType.ANTI):
        return left_schema

    from mountainash.relations.core.join_layout import asof_right_name_map, keyed_layout_applies, layout_for_node

    if node.join_type == JoinType.ASOF:
        names = asof_right_name_map(node, list(left_schema), list(right_schema))
        return {**left_schema, **{final: right_schema[name] for name, final in names.items()}}

    if keyed_layout_applies(node):
        layout = layout_for_node(node, list(left_schema), list(right_schema))
        keyed: dict[str, _DetailedDtype | SchemaTypeStatus] = dict(left_schema)
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

    result: dict[str, _DetailedDtype | SchemaTypeStatus] = dict(left_schema)

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
