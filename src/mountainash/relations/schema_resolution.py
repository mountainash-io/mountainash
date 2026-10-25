"""Shared schema resolution using structural evidence and the ordinary compiler."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from mountainash.core.dtypes import SchemaTypeStatus, dtype_is_complete
from mountainash.core.types import (
    is_ibis_table, is_narwhals_dataframe, is_narwhals_lazyframe,
    is_pandas_dataframe, is_polars_dataframe, is_polars_lazyframe, is_pyarrow_table,
)
from mountainash.relations.core.errors import CompileRequiresExecutionError, IncompleteSchemaError
from mountainash.relations.core.execution.preparation import ExecutionPhase
from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
from mountainash.relations.schema_inference import (
    _aggregate_input_names, infer_schema,
)


@dataclass(frozen=True)
class _SchemaEvidence:
    schema: dict[str, Any]
    names_complete: bool
    reason: str = "Native metadata does not establish every output dtype parameter."
    authoritative: bool = True

    @property
    def unresolved(self) -> tuple[str, ...]:
        missing = tuple(name for name, dtype in self.schema.items() if not dtype_is_complete(dtype))
        return missing or (() if self.authoritative else tuple(self.schema))

    @property
    def complete(self) -> bool:
        return self.authoritative and self.names_complete and not self.unresolved


def _is_native(value: Any) -> bool:
    return any(predicate(value) for predicate in (
        is_polars_dataframe, is_polars_lazyframe, is_pandas_dataframe,
        is_pyarrow_table, is_ibis_table, is_narwhals_dataframe, is_narwhals_lazyframe,
    ))


def _describe_native(system: Any, native: Any, location: Any) -> _SchemaEvidence:
    """Physical output evidence from the relation system that owns ``native``."""
    return _SchemaEvidence(system.describe_output_schema(native, location=location), _is_native(native))


def _source_evidence(node: Any) -> _SchemaEvidence:
    """Describe a native source through the system its actual location selects."""
    from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver

    location = LocationResolver(IdentityTokens()).resolve(node)
    system = get_relation_system(location.family)(dialect=location.dialect)
    return _describe_native(system, node.dataframe, location)


def _structural_evidence(relation: Any) -> _SchemaEvidence:
    from mountainash.relations.core.relation_nodes import (
        FetchRelNode, FilterRelNode, JoinRelNode, ProjectRelNode, ReadRelNode,
        SetRelNode, SortRelNode,
    )
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ExtensionRelNode, RefRelNode, SourceRelNode,
    )
    from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL as RM

    preserving_extensions = {
        RM.WITH_ROW_INDEX, RM.SAMPLE, RM.TOP_K, RM.FETCH_FROM_END,
        RM.DROP_NULLS, RM.DROP_NANS,
    }

    dag = getattr(relation, "_dag", None)
    if dag is not None:
        from mountainash.relations.dag.introspection import structural_schema

        def ref_resolver(name):
            return structural_schema(dag, name)

        def identity_resolver(name):
            return dag.relations[name]._node
    else:
        ref_resolver = identity_resolver = None

    def preserves_types(node: Any, active: frozenset[str] = frozenset()) -> bool:
        if isinstance(node, ReadRelNode):
            # Logical SQL source types can differ from the physical output.
            # Keep structural consumers cheap; public inspection describes SQL.
            return _is_native(node.dataframe) and not is_ibis_table(node.dataframe)
        if isinstance(node, RefRelNode):
            return (
                dag is not None and node.name not in active
                and preserves_types(identity_resolver(node.name), active | {node.name})
            )
        if isinstance(node, (FilterRelNode, SortRelNode, FetchRelNode, ProjectRelNode)):
            return preserves_types(node.input, active)
        if isinstance(node, SourceRelNode):
            return _aggregate_input_names(
                node, identity_resolver=identity_resolver, _resolver=name_resolver,
            ) is not None
        if isinstance(node, ExtensionRelNode) and node.operation in preserving_extensions:
            return preserves_types(node.input, active)
        return False

    def changes_types(node: Any, active: frozenset[str] = frozenset()) -> bool:
        if isinstance(node, (JoinRelNode, SetRelNode)):
            return True
        if isinstance(node, ExtensionRelNode) and node.operation not in preserving_extensions:
            return True
        if isinstance(node, RefRelNode) and dag is not None and node.name not in active:
            return changes_types(identity_resolver(node.name), active | {node.name})
        return any(changes_types(child, active) for child in node.children())

    node = relation._node
    if isinstance(node, ReadRelNode) and _is_native(node.dataframe):
        try:
            return _source_evidence(node)
        except CompileRequiresExecutionError as error:
            from mountainash.typespec.source_shape import extract_source_names

            names = extract_source_names(node.dataframe)
            return _SchemaEvidence(
                dict.fromkeys(names if names is not None else (), SchemaTypeStatus.UNKNOWN),
                names is not None, str(error), authoritative=False,
            )
    from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver

    name_resolver = LocationResolver(IdentityTokens(), identity_resolver=identity_resolver)
    schema = infer_schema(
        node, ref_resolver, identity_resolver=identity_resolver, _name_resolver=name_resolver,
    )
    if preserves_types(node):
        return _SchemaEvidence(schema, True)
    output_node = node
    while isinstance(output_node, RefRelNode) and identity_resolver is not None:
        output_node = identity_resolver(output_node.name)
    names = _aggregate_input_names(
        output_node, identity_resolver=identity_resolver, _resolver=name_resolver,
    )
    if changes_types(node):
        original = schema
        schema = {name: SchemaTypeStatus.UNKNOWN for name in schema}
        if isinstance(output_node, ExtensionRelNode):
            if output_node.operation is RM.WITH_ROW_INDEX:
                ordinal = output_node.options.get("name", "index")
                schema[ordinal] = original[ordinal]
            elif output_node.operation not in preserving_extensions:
                schema = {}
    return _SchemaEvidence(schema, names is not None, authoritative=False)


def _compiled_evidence(relation: Any, *, execute: bool) -> _SchemaEvidence:
    from mountainash.relations.core.relation_api.relation import (
        _compiler_identity, _finish_terminal, _guard_native_terminal,
    )

    phase = ExecutionPhase.EXECUTE if execute else ExecutionPhase.SCHEMA
    result, visitor = relation._compile_and_execute_with_visitor(
        phase=phase, retain_execution_scope=True,
    )

    def inspect() -> _SchemaEvidence:
        # The location and system established by compilation, not re-derived from the result.
        location = visitor.execution.prepared.locations[visitor.execution_key]
        if not execute:
            from polars.exceptions import ColumnNotFoundError

            try:
                evidence = _describe_native(visitor.backend, result, location)
            except ColumnNotFoundError as error:
                visitor.metadata_session.raise_if_bounded(error)
                raise
            if not visitor.metadata_session.schema_complete:
                return replace(
                    evidence, names_complete=False, authoritative=False,
                    reason="Resource schema discovery supplied only bounded evidence.",
                )
            return evidence
        from mountainash.core.limitations import enrich_materialization
        from mountainash.relations.core.materialization import (
            MaterializationPurpose, MaterializationScope, materialize_native,
        )

        def materialize() -> _SchemaEvidence:
            _guard_native_terminal(visitor.structured_field_plans)
            with MaterializationScope() as scope:
                native = materialize_native(
                    result, _compiler_identity(visitor), MaterializationPurpose.LOGICAL_TERMINAL,
                    execution_context=visitor.execution_context, scope=scope,
                )
                return _describe_native(visitor.backend, native.value, location)

        return enrich_materialization(
            visitor.backend, materialize,
            diagnostic_trace=visitor._active_diagnostic_trace(),
            residue_checks=visitor.terminal_residue_checks(),
            execution_context=visitor.execution_context,
        )

    return _finish_terminal(visitor, inspect, release_owned_on_success=True)


def resolve_schema(
    relation: Any, *, require_complete: bool = False, allow_execution: bool = False,
) -> dict[str, Any]:
    """Resolve output evidence without turning metadata failures into execution."""
    projection_error = None
    try:
        evidence = _structural_evidence(relation)
    except IncompleteProjectionSchemaError as error:
        projection_error = error
        evidence = _SchemaEvidence({}, False, str(error))
    if evidence.complete:
        return dict(evidence.schema)

    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
    from mountainash.relations.dag.errors import RelationDAGRequired
    if isinstance(relation._node, RefRelNode) and getattr(relation, "_dag", None) is None:
        evidence = _SchemaEvidence(
            {}, False,
            f"Reference {relation._node.name!r} needs a DAG binding; execution cannot supply it.",
        )
    else:
        try:
            evidence = _compiled_evidence(relation, execute=False)
        except CompileRequiresExecutionError as error:
            evidence = replace(evidence, reason=str(error))
        except RelationDAGRequired as error:
            if require_complete:
                raise IncompleteSchemaError(
                    fields=evidence.unresolved, names_complete=evidence.names_complete,
                    reason=f"{error}; execution cannot supply a missing binding.",
                ) from error
            if projection_error is not None:
                raise projection_error
            return dict(evidence.schema)
        if not evidence.complete and allow_execution:
            evidence = _compiled_evidence(relation, execute=True)
    if require_complete and not evidence.complete:
        raise IncompleteSchemaError(
            fields=evidence.unresolved, names_complete=evidence.names_complete,
            reason=evidence.reason,
        )
    if projection_error is not None and not evidence.names_complete:
        raise projection_error
    return dict(evidence.schema)
