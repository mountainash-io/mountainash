"""Nonexecuting placement and whole-tree capability witnesses."""
from mountainash.core.capabilities.applicability import unbounded

import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import Clause, ClauseOp, PolicyAction, PolicyConsumer, Predicate
from mountainash.core.capabilities.policy import CapabilityPolicy
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON as FK
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CONDITIONAL
from mountainash.relations.core.errors import (
    CompileRequiresExecutionError, ConflictingExecutionTargetError,
    UnresolvedExecutionLocationError,
)
from mountainash.relations.core.execution.preparation import (
    ExecutionPhase, prepare_execution, render_execution,
)
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL as RS


def test_late_union_transfer_is_detected_without_executing_earlier_inputs(monkeypatch):
    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    root = ma.concat([ma.relation(a), ma.relation(a).filter(ma.col("id") > 0), ma.relation(b)])._node

    def forbidden(*args, **kwargs):
        raise AssertionError("preparation executed data")

    monkeypatch.setattr(type(a), "to_pyarrow", forbidden)
    monkeypatch.setattr(type(a), "cache", forbidden)
    with pytest.raises(CompileRequiresExecutionError, match="collect"):
        prepare_execution(root, phase=ExecutionPhase.COMPILE)
    text = render_execution(prepare_execution(root, phase=ExecutionPhase.EXPLAIN))
    assert "ibis-duckdb" in text and "ibis-sqlite" in text
    assert "transfer" in text.lower()


@pytest.mark.parametrize("shape", ["join", "union", "nested"])
@pytest.mark.parametrize("phase", list(ExecutionPhase))
@pytest.mark.parametrize("public_path", [False, True])
def test_late_known_gate_precedes_every_export(monkeypatch, shape, phase, public_path):
    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [1]}, "b")
    early, late = ma.relation(a), ma.relation(b).filter(ma.col("id") > 0)
    if shape == "union":
        rel = ma.concat([early, late])
    else:
        if shape == "nested":
            early = early.join(b, on="id", execute_on="right")
        rel = early.join(late, on="id", execute_on="right")
    exports = []

    def forbidden_export(*args, **kwargs):
        exports.append(True)
        raise AssertionError("source exported before late capability gate")

    monkeypatch.setattr(type(a), "to_pyarrow", forbidden_export)
    monkeypatch.setattr(type(a), "cache", forbidden_export)
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.relations.backends.capabilities.ibis.dialects.ibis_sqlite.substrait.relation",
            Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite")),
            CapabilitySegment(Domain.RELATION, policies=(CapabilityPolicyRule(key=CapabilityKey(RS.FILTER, "*"),
            level=CapabilityLevel.UNSUPPORTED, message="P3 late SQLite filter gate",
            consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK, applicability=unbounded),)),
        ))
        with pytest.raises(BackendCapabilityError, match="P3 late SQLite filter gate") as caught:
            if public_path:
                if phase is ExecutionPhase.EXECUTE:
                    rel.collect()
                elif phase is ExecutionPhase.COMPILE:
                    rel.compile()
                else:
                    rel.explain()
            else:
                prepare_execution(rel._node, phase=phase)
        assert caught.value.function_key is RS.FILTER
        assert exports == []
    finally:
        CapabilityRegistry.restore(snapshot)


def test_override_checks_inner_explicit_targets():
    a = REGISTRY["polars"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-duckdb"].build({"id": [1]}, "b")
    inner = ma.relation(a).join(b, on="id", execute_on="left")
    root = inner.join(b, on="id", execute_on="right")._node
    for backend in ("polars", "ibis"):
        with pytest.raises(ConflictingExecutionTargetError):
            prepare_execution(root, phase=ExecutionPhase.EXECUTE, backend=backend)


def test_matching_override_keeps_selected_connection():
    a = REGISTRY["polars"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [1]}, "b")
    root = ma.relation(a).join(b, on="id", execute_on="right")._node
    prepared = prepare_execution(root, phase=ExecutionPhase.EXPLAIN, backend="ibis")
    assert prepared.locations["root"].connection is b._find_backend(use_default=False)
    assert prepared.locations["root"].dialect == "ibis-sqlite"


@pytest.mark.parametrize("phase", [ExecutionPhase.COMPILE, ExecutionPhase.EXECUTE])
def test_connectionless_authority_rejected_without_default(phase):
    import ibis
    peer = REGISTRY["polars"].build({"id": [1]}, "peer")
    root = ma.relation(ibis.memtable({"id": [1]})).join(peer, on="id")._node
    with pytest.raises(UnresolvedExecutionLocationError):
        prepare_execution(root, phase=phase)
    assert "unresolved" in render_execution(prepare_execution(root, phase=ExecutionPhase.EXPLAIN))


def test_raw_mapping_peer_uses_declared_ingress_without_reading_rows(monkeypatch):
    bound = REGISTRY["ibis-sqlite"].build({"id": [1]}, "bound")
    raw = {"id": [2]}
    relation = ma.relation(bound).join(raw, on="id")

    def forbidden(*args, **kwargs):
        raise AssertionError("placement read rows")

    monkeypatch.setattr(type(bound), "to_pyarrow", forbidden)
    prepared = prepare_execution(relation._node, phase=ExecutionPhase.EXPLAIN)
    peer_key = "root/right"
    assert prepared.locations[peer_key].family is CONST_BACKEND.POLARS
    assert prepared.locations[peer_key].connection is None
    assert prepared.transfers[peer_key].destination.connection is bound._find_backend(use_default=False)
    assert not prepared.transfers[peer_key].requires_execution
    assert prepare_execution(relation._node, phase=ExecutionPhase.COMPILE)


@pytest.mark.parametrize("source_name", ["narwhals-lazy", "polars-lazy"])
def test_lazy_operand_to_eager_narwhals_is_execution_required(source_name):
    target = REGISTRY["narwhals-pandas"].build({"id": [1]}, "target")
    source = REGISTRY[source_name].build({"id": [2]}, "source")
    root = ma.relation(target).join(source, on="id")._node
    prepared = prepare_execution(root, phase=ExecutionPhase.EXPLAIN)
    requirement = prepared.transfers["root/right"]
    assert requirement.requires_execution
    assert requirement.destination.dialect == "narwhals-pandas"
    with pytest.raises(CompileRequiresExecutionError, match="collect"):
        prepare_execution(root, phase=ExecutionPhase.COMPILE)


@pytest.mark.parametrize("shape", ["join", "union", "targeted_union"])
def test_compile_rejects_deferred_boundary_but_explain_keeps_recipe(shape):
    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    left = ma.relation(a)
    if shape == "targeted_union":
        left = left.join(b, on="id", execute_on="right")
    rel = left.join(b, on="id") if shape == "join" else ma.concat([left, ma.relation(b if shape == "union" else a)])
    prepared = prepare_execution(rel._node, phase=ExecutionPhase.EXPLAIN)
    assert prepared.transfers
    assert "transfer" in render_execution(prepared)
    with pytest.raises(CompileRequiresExecutionError, match="collect"):
        prepare_execution(rel._node, phase=ExecutionPhase.COMPILE)


def test_expanded_reference_preflights_without_executing():
    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    dag = ma.RelationDAG()
    dag.add("earlier", ma.relation(a))
    dag.add("later", ma.relation(b).filter(ma.col("id") > 0))
    root = ma.concat([dag.ref("earlier"), dag.ref("later")])._node
    prepared = prepare_execution(root, phase=ExecutionPhase.EXPLAIN,
                                 identity_resolver=lambda name: dag.relations[name]._node)
    assert any("/ref/" in key for key in prepared.nodes)
    with pytest.raises(CompileRequiresExecutionError, match="collect"):
        prepare_execution(root, phase=ExecutionPhase.COMPILE,
                          identity_resolver=lambda name: dag.relations[name]._node)


def test_disabled_policy_does_not_preflight_selected_gate():
    from mountainash.core.capabilities.policy import _new_execution_context

    a = REGISTRY["ibis-sqlite"].build({"id": [1]}, "a")
    root = ma.relation(a).filter(ma.col("id") > 0)._node
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.relations.backends.capabilities.ibis.dialects.ibis_sqlite.substrait.relation",
            Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite")),
            CapabilitySegment(Domain.RELATION, policies=(CapabilityPolicyRule(key=CapabilityKey(RS.FILTER, "*"), level=CapabilityLevel.UNSUPPORTED, message="disabled filter gate",
            consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK, applicability=unbounded),)),
        ))
        context = _new_execution_context(a, policy=CapabilityPolicy.trusted())
        assert prepare_execution(root, phase=ExecutionPhase.EXPLAIN, execution_context=context)
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("predicate,blocks", [
    (Predicate((Clause("y", ClauseOp.IS_LITERAL),)), True),
    (Predicate((Clause("__operand_types__.y.logical_kind", ClauseOp.EQ, "integer"),)), False),
])
def test_embedded_expression_gate_uses_ast_evidence_only(predicate, blocks):
    a = REGISTRY["ibis-sqlite"].build({"id": [1]}, "a")
    rel = ma.relation(a).filter(ma.col("id") > 0)
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_sqlite.substrait.comparison",
            Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite")),
            CapabilitySegment(Domain.COMPARISON, policies=(CapabilityPolicyRule(key=CapabilityKey(FK.GT, "y", Selector("predicate", predicate)),
            level=CapabilityLevel.UNSUPPORTED, message="AST-known literal comparison gate",
            consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK, applicability=unbounded),)),
        ))
        if blocks:
            with pytest.raises(BackendCapabilityError, match="AST-known literal comparison gate") as caught:
                prepare_execution(rel._node, phase=ExecutionPhase.EXPLAIN)
            assert caught.value.function_key is FK.GT
        else:
            assert prepare_execution(rel._node, phase=ExecutionPhase.EXPLAIN)
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("scope", ["output", "source"])
def test_terminal_override_gates_embedded_expression_at_actual_operation(scope):
    source = REGISTRY["ibis-duckdb"].build({"id": [1]}, "source")
    expression = ma.col("id") > 0
    rel = ma.relation(source).filter(expression)
    if scope == "source":
        rel = rel.select("id")
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.polars.dialects.polars.substrait.comparison",
            Scope(CONST_BACKEND.POLARS, Dialect("polars")),
            CapabilitySegment(Domain.COMPARISON, policies=(CapabilityPolicyRule(key=CapabilityKey(FK.GT, "*"), level=CapabilityLevel.UNSUPPORTED, message="target polars comparison gate",
            consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK, applicability=unbounded),)),
        ))
        if scope == "output":
            with pytest.raises(BackendCapabilityError, match="target polars comparison gate"):
                prepare_execution(rel._node, phase=ExecutionPhase.EXPLAIN, backend="polars")
        else:
            prepare_execution(rel._node, phase=ExecutionPhase.EXPLAIN, backend="polars")
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("phase", list(ExecutionPhase))
def test_late_implicit_if_then_gate_precedes_transfer(phase, monkeypatch):
    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    conditional = ma.when(ma.col("id") > 0).then(1).otherwise(0)
    root = ma.concat([ma.relation(a), ma.relation(b).select(conditional.alias("id"))])._node

    def forbidden(*args, **kwargs):
        raise AssertionError("transfer executed before IfThen gate")

    monkeypatch.setattr(type(a), "to_pyarrow", forbidden)
    monkeypatch.setattr(type(b), "to_pyarrow", forbidden)
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_sqlite.substrait.conditional",
            Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite")),
            CapabilitySegment(Domain.CONDITIONAL, policies=(CapabilityPolicyRule(key=CapabilityKey(FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE, "*"),
            level=CapabilityLevel.UNSUPPORTED, message="late implicit IfThen gate", consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK, applicability=unbounded),)),
        ))
        with pytest.raises(BackendCapabilityError, match="late implicit IfThen gate") as caught:
            prepare_execution(root, phase=phase)
        assert caught.value.function_key is FKEY_SUBSTRAIT_CONDITIONAL.IF_THEN_ELSE
    finally:
        CapabilityRegistry.restore(snapshot)


def test_policy_is_frozen_once_across_distinct_target_observations(monkeypatch):
    from mountainash.relations.core.execution import preparation

    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    root = ma.concat([ma.relation(a), ma.relation(b)])._node
    calls = []

    def changing_policy():
        calls.append(True)
        return CapabilityPolicy.checked() if len(calls) == 1 else CapabilityPolicy.trusted()

    monkeypatch.setattr(preparation, "_resolve_policy", changing_policy)
    prepared = prepare_execution(root, phase=ExecutionPhase.EXPLAIN)
    left = prepared.context_for(prepared.locations["root/inputs/0"])
    right = prepared.context_for(prepared.locations["root/inputs/1"])
    assert len(calls) == 1
    assert left.policy is right.policy
    assert left.target.owner is a._find_backend(use_default=False)
    assert right.target.owner is b._find_backend(use_default=False)
    assert left.target.identity.dialect == "ibis-duckdb"
    assert right.target.identity.dialect == "ibis-sqlite"
    assert left is not right


def test_supplied_context_policy_is_reused_with_foreign_target_observation(monkeypatch):
    from mountainash.core.capabilities.policy import _new_execution_context
    from mountainash.relations.core.execution import preparation

    a = REGISTRY["ibis-duckdb"].build({"id": [1]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    context = _new_execution_context(a, policy=CapabilityPolicy.trusted())

    def forbidden_policy():
        raise AssertionError("an execution context already froze the policy")

    monkeypatch.setattr(preparation, "_resolve_policy", forbidden_policy)
    root = ma.relation(a).join(b, on="id")._node
    prepared = prepare_execution(root, phase=ExecutionPhase.EXPLAIN, execution_context=context)
    assert prepared.context_for(prepared.locations["root/left"]) is context
    right = prepared.context_for(prepared.locations["root/right"])
    assert right.policy is context.policy
    assert right.target.owner is b._find_backend(use_default=False)
    assert right.target.identity.dialect == "ibis-sqlite"
