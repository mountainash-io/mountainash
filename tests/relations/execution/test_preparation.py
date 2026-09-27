"""Nonexecuting placement and whole-tree capability witnesses."""

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
def test_late_known_gate_precedes_every_export(monkeypatch, shape, phase):
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
            CapabilitySegment(Domain.RELATION, policies=(CapabilityPolicyRule(
                key=CapabilityKey(RS.FILTER, "*"),
                level=CapabilityLevel.UNSUPPORTED,
                since="2026-09-27", message="P3 late SQLite filter gate",
                consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK,
            ),)),
        ))
        with pytest.raises(BackendCapabilityError, match="P3 late SQLite filter gate") as caught:
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
            CapabilitySegment(Domain.RELATION, policies=(CapabilityPolicyRule(
                key=CapabilityKey(RS.FILTER, "*"), level=CapabilityLevel.UNSUPPORTED,
                since="2026-09-27", message="disabled filter gate",
                consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK,
            ),)),
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
            CapabilitySegment(Domain.COMPARISON, policies=(CapabilityPolicyRule(
                key=CapabilityKey(FK.GT, "y", Selector("predicate", predicate)),
                level=CapabilityLevel.UNSUPPORTED, since="2026-09-27",
                message="AST-known literal comparison gate",
                consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK,
            ),)),
        ))
        if blocks:
            with pytest.raises(BackendCapabilityError, match="AST-known literal comparison gate") as caught:
                prepare_execution(rel._node, phase=ExecutionPhase.EXPLAIN)
            assert caught.value.function_key is FK.GT
        else:
            assert prepare_execution(rel._node, phase=ExecutionPhase.EXPLAIN)
    finally:
        CapabilityRegistry.restore(snapshot)
