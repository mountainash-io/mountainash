"""Execution-local metadata remains source-owned across visitor boundaries."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.conform.diagnostics import OperationDiagnostic, OperationDiagnosticTrace
from mountainash.conform.expressions import MaterializationResidueCheck
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.execution.location import ExecutionLocation, IdentityTokens
from mountainash.relations.core.execution.metadata import MetadataSession
from mountainash.relations.core.materialization import ExecutionForm
from mountainash.relations.core.structured_lineage import propagate_owned_residue
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def test_conform_identity_is_execution_local_and_shared_across_visitors():
    metadata = MetadataSession(IdentityTokens())
    first, second = object(), object()
    assert metadata.conform_id(first) == metadata.conform_id(first)
    assert metadata.conform_id(first) != metadata.conform_id(second)


def test_trace_extend_preserves_original_records_in_order():
    records = tuple(OperationDiagnostic(None, name, None, name, (), None, "payload", "array", "")
                    for name in ("source-a", "source-b"))
    trace = OperationDiagnosticTrace()
    trace.extend(records)
    assert trace.records[0] is records[0]
    assert trace.records[1] is records[1]


def test_adoption_preserves_distinct_diagnostics_and_source_owned_checks():
    tokens = IdentityTokens()
    session = MetadataSession(tokens)
    a = ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.LAZY, "bound")
    b = ExecutionLocation(CONST_BACKEND.IBIS, "ibis-duckdb", ExecutionForm.DEFERRED, "bound")
    child_nodes = (object(), object())
    children = []
    for index, location in enumerate((a, b)):
        record = OperationDiagnostic(None, location.family.value, location.dialect,
                                     session.conform_id(child_nodes[index]), (), None, "payload", "array", "")
        trace = OperationDiagnosticTrace()
        trace.extend((record,))
        marker = f"__ma_residue_{index}"
        check = MaterializationResidueCheck(None, "payload", marker)
        visitor = SimpleNamespace(diagnostic_traces={(location.family, location.dialect): trace},
                                  residue_checks=[check], residue_check_nodes={marker: record.conform_node_id},
                                  owned_residue_checks=[], drift_reports=[], structured_field_plans={},
                                  _structured_plans_by_node={})
        children.append(session.capture(visitor, owner_key=f"root/{index}", location=location, value=object()))
    parent = SimpleNamespace(diagnostic_traces={}, residue_checks=[], residue_check_nodes={},
                             owned_residue_checks=[], drift_reports=[], structured_field_plans={},
                             _structured_plans_by_node={})
    for node, child in zip(child_nodes, children):
        session.adopt(parent, node, child)
    session.adopt(parent, child_nodes[0], children[0])
    captured = session.capture(parent, owner_key="root", location=a, value=object())
    assert [r for r in captured.metadata.diagnostic_records] == [
        children[0].metadata.diagnostic_records[0], children[1].metadata.diagnostic_records[0]
    ]
    assert captured.metadata.diagnostic_records[1] is children[1].metadata.diagnostic_records[0]
    assert [(r.owner_key, r.source_location) for r in captured.metadata.owned_checks] == [
        ("root/0", a), ("root/1", b)
    ]


def test_join_suffix_maps_source_marker_without_changing_owner():
    tokens = IdentityTokens()
    session = MetadataSession(tokens)
    source = ExecutionLocation(CONST_BACKEND.IBIS, "ibis-duckdb", ExecutionForm.DEFERRED, "bound")
    owner = session.capture(SimpleNamespace(diagnostic_traces={}, residue_checks=[
        MaterializationResidueCheck(None, "payload", "__ma_residue_0")],
        residue_check_nodes={}, owned_residue_checks=[], drift_reports=[],
        structured_field_plans={}, _structured_plans_by_node={}),
        owner_key="root/right", location=source, value=object())
    join = ma.relation({"id": [1], "__ma_residue_0": [False]}).join(
        {"id": [1], "payload": ["[1]"], "__ma_residue_0": [True]}, on="id", suffix="_foreign"
    )._node
    result = propagate_owned_residue(join, [(), owner.metadata.owned_checks])
    assert result[0].check.marker == "__ma_residue_0_foreign"
    assert result[0].owner_key == "root/right"
    assert result[0].source_location is source


def test_pending_source_check_cannot_be_dropped_by_parent_projection():
    location = ExecutionLocation(CONST_BACKEND.IBIS, "ibis-duckdb", ExecutionForm.DEFERRED, "bound")
    session = MetadataSession(IdentityTokens())
    child = ma.relation({"id": [1], "payload": ["[1]"]})
    check = MaterializationResidueCheck(None, "payload", "__ma_residue_0")
    visitor = SimpleNamespace(diagnostic_traces={}, residue_checks=[check], residue_check_nodes={},
                              owned_residue_checks=[], drift_reports=[], structured_field_plans={},
                              _structured_plans_by_node={})
    envelope = session.capture(visitor, owner_key="source", location=location, value=object())
    with pytest.raises(ValueError, match="must be checked"):
        propagate_owned_residue(child.select("id")._node, [envelope.metadata.owned_checks])
    assert envelope.metadata.owned_checks[0].check is check
    assert envelope.metadata.owned_checks[0].source_location is location


def test_visitor_rejects_projection_removing_adopted_marker_before_native_dispatch(backend_factory):
    """Polars-only visitor wiring: no expression compilation or backend semantics."""
    from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
    from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
    from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
    from mountainash.relations.core.relation_system.relation_mapping.registry import RelationOperationRegistry
    from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor

    frame = backend_factory.create({"id": [1], "payload": ["[1]"]}, "polars")
    child = ma.relation(frame)
    parent = child.select("id")._node
    context = _new_execution_context(frame, family_override=CONST_BACKEND.POLARS,
                                     policy=CapabilityPolicy.trusted())
    system = get_expression_system(CONST_BACKEND.POLARS)(execution_context=context)
    visitor = UnifiedRelationVisitor(
        get_relation_system(CONST_BACKEND.POLARS)(),
        UnifiedExpressionVisitor(system, input_data=frame, execution_context=context),
        execution_context=context,
    )
    session = MetadataSession(IdentityTokens())
    marker = MaterializationResidueCheck(None, "payload", "__ma_residue_0")
    source = SimpleNamespace(diagnostic_traces={}, residue_checks=[marker],
                             owned_residue_checks=[], drift_reports=[], structured_field_plans={},
                             _structured_plans_by_node={})
    location = ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.LAZY, "bound")
    session.adopt(visitor, parent.input, session.capture(
        source, owner_key="source", location=location, value=frame.lazy(),
    ))
    with pytest.raises(ValueError, match="must be checked"):
        visitor._prepare_transport_lineage(parent, RelationOperationRegistry.get(parent.operation_key))


def test_capture_is_immutable_snapshot_not_live_visitor_state():
    session = MetadataSession(IdentityTokens())
    location = ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.LAZY, "bound")
    plans = {"payload": object()}
    trace = OperationDiagnosticTrace()
    record = OperationDiagnostic(None, "polars", "polars", "source", (), None, "payload", "array", "")
    trace.extend((record,))
    visitor = SimpleNamespace(diagnostic_traces={(CONST_BACKEND.POLARS, "polars"): trace},
                              residue_checks=[], owned_residue_checks=[], drift_reports=[],
                              structured_field_plans=plans, _structured_plans_by_node={})
    first = session.capture(visitor, owner_key="source", location=location, value=object())
    plans.clear()
    trace.extend((OperationDiagnostic(None, "polars", "polars", "later", (), None, "x", "", ""),))
    assert first.metadata.diagnostic_records == (record,)
    assert set(first.metadata.structured_field_plans) == {"payload"}


def test_adopt_keeps_child_resource_dependencies_without_releasing_them():
    session = MetadataSession(IdentityTokens())
    location = ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.LAZY, "bound")
    resource = object()
    visitor = SimpleNamespace(diagnostic_traces={}, residue_checks=[], owned_residue_checks=[],
                              drift_reports=[], structured_field_plans={}, owned_resources=[resource],
                              _structured_plans_by_node={})
    child = session.capture(visitor, owner_key="source", location=location, value=object())
    visitor.owned_resources.clear()
    parent = SimpleNamespace(diagnostic_traces={}, residue_checks=[], owned_residue_checks=[],
                             drift_reports=[], structured_field_plans={},
                             _structured_plans_by_node={})
    session.adopt(parent, object(), child)
    session.adopt(parent, object(), child)
    assert session.capture(parent, owner_key="parent", location=location, value=object()).metadata.resources == (resource,)


@pytest.mark.parametrize("backend_name", list(REGISTRY))
def test_two_child_structured_origins_survive_join_adoption(backend_name, backend_factory):
    """Metadata plumbing only: Task 6 wires contextual join compilation."""
    from mountainash.core.backend_detection import identify_backend
    from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
    from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
    from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
    from mountainash.relations.core.relation_system.relation_mapping.registry import RelationOperationRegistry
    from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor

    spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    first = ma.relation(backend_factory.create({"id": [1], "payload": ["[1]"]}, backend_name)).conform(spec)
    second = ma.relation(backend_factory.create({"id": [1], "payload": ["[2]"]}, backend_name)).conform(spec)
    session = MetadataSession(IdentityTokens())
    children = []
    for index, rel in enumerate((first, second)):
        frame = rel._node.input.dataframe
        family = identify_backend(frame)
        context = _new_execution_context(frame, family_override=family, policy=CapabilityPolicy.trusted())
        system = get_expression_system(family)(execution_context=context)
        visitor = UnifiedRelationVisitor(
            get_relation_system(family)(),
            UnifiedExpressionVisitor(system, input_data=frame, execution_context=context),
            execution_context=context, metadata_session=session,
        )
        native = visitor.visit(rel._node)
        location = ExecutionLocation(family, backend_name, ExecutionForm.DEFERRED, "bound")
        children.append(session.capture(visitor, owner_key=f"root/{index}", location=location, value=native))

    parent = UnifiedRelationVisitor(
        get_relation_system(family)(),
        UnifiedExpressionVisitor(system, input_data=frame, execution_context=context),
        execution_context=context, metadata_session=session,
    )
    joined = first.join(second, on="id", suffix="_right")._node
    session.adopt(parent, joined.left, children[0])
    session.adopt(parent, joined.right, children[1])
    op = RelationOperationRegistry.get(joined.operation_key)
    parent._prepare_transport_lineage(joined, op)
    parent._complete_transport_lineage(joined, op)
    merged = parent.structured_field_plans
    assert set(merged) == {"payload", "payload_right"}
    assert merged["payload"].origin_node_id != merged["payload_right"].origin_node_id
    assert merged["payload"].origin_node_id == session.conform_id(joined.left)
    assert merged["payload_right"].origin_node_id == session.conform_id(joined.right)
