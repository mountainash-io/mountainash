"""Non-executing placement and physical Ibis binding contracts."""
from __future__ import annotations

import ibis
import pyarrow as pa
import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.core.constants import CONST_BACKEND, ExecutionTarget, JoinType
from mountainash.relations.core.errors import (
    ConflictingExecutionTargetError, UnresolvedExecutionLocationError,
)
from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.relations.core.relation_nodes.substrait.reln_join import JoinRelNode
from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode, ResourceReadRelNode
from mountainash.relations.dag.errors import RelationDAGRequired, UnknownRelationRef
from mountainash.typespec.datapackage import DataResource


IBIS_BACKENDS = [name for name, spec in REGISTRY.items() if spec.family == "ibis"]


@pytest.mark.parametrize("backend_name", IBIS_BACKENDS)
def test_equal_names_do_not_make_connections_compatible(backend_name):
    left = REGISTRY[backend_name].build({"id": [1]}, "same")
    right = REGISTRY[backend_name].build({"id": [2]}, "same")
    resolver = LocationResolver(IdentityTokens())
    a = resolver.resolve(ma.relation(left)._node)
    b = resolver.resolve(ma.relation(right)._node)
    assert a.connection is left._find_backend(use_default=False)
    assert b.connection is right._find_backend(use_default=False)
    assert a.connection is not b.connection
    assert a.key != b.key
    assert a.capability_identity == b.capability_identity
    assert a.binding == b.binding == "bound"


@pytest.mark.parametrize("backend_name", IBIS_BACKENDS)
def test_shared_memory_plan_borrows_each_peer_not_first_peer(backend_name):
    memory = ma.relation(ibis.memtable(pa.table({"id": [1, 2]}))).filter(ma.col("id") > 1)
    a = REGISTRY[backend_name].build({"id": [2]}, "a")
    b = REGISTRY[backend_name].build({"id": [2]}, "b")
    resolver = LocationResolver(IdentityTokens())
    x = resolver.resolve(memory.join(a, on="id", execute_on="left")._node)
    y = resolver.resolve(ma.relation(b).join(memory, on="id", execute_on="right")._node)
    assert x.connection is a._find_backend(use_default=False)
    assert y.connection is b._find_backend(use_default=False)
    assert x.key != y.key
    assert resolver.resolve(memory._node).binding == "memory"


def test_identity_tokens_retain_identity_not_value_equality():
    tokens = IdentityTokens()
    first, second = [1], [1]
    assert tokens.token(first) == tokens.token(first)
    assert tokens.token(second) != tokens.token(first)


def test_raw_source_keeps_polars_ingress_without_borrowing_ibis():
    bound = REGISTRY["ibis-duckdb"].build({"id": [1]}, "bound")
    resolver = LocationResolver(IdentityTokens())
    assert resolver.resolve(ma.relation({"id": [1]})._node).family is CONST_BACKEND.POLARS
    assert resolver.resolve(ma.relation(bound).join({"id": [1]}, on="id")._node).connection is bound._find_backend(use_default=False)


@pytest.mark.parametrize("backend_name", IBIS_BACKENDS)
def test_join_default_and_unary_parent_follow_selected_nested_output(backend_name):
    a = REGISTRY[backend_name].build({"id": [1]}, "a")
    b = REGISTRY[backend_name].build({"id": [1]}, "b")
    resolver = LocationResolver(IdentityTokens())
    inner = ma.relation(a).join(b, on="id", execute_on="right")
    assert resolver.resolve(inner.filter(ma.col("id") > 0)._node).connection is b._find_backend(use_default=False)
    assert resolver.resolve(inner.join(a, on="id")._node).connection is b._find_backend(use_default=False)
    assert resolver.resolve(inner.join(a, on="id", execute_on="right")._node).connection is a._find_backend(use_default=False)


@pytest.mark.parametrize("backend_name", IBIS_BACKENDS)
def test_set_uses_first_input_or_first_bound_peer(backend_name):
    a = REGISTRY[backend_name].build({"id": [1]}, "a")
    b = REGISTRY[backend_name].build({"id": [2]}, "b")
    memory = ma.relation(ibis.memtable(pa.table({"id": [3]})))
    resolver = LocationResolver(IdentityTokens())
    for inputs, expected in (
        ([ma.relation(a), ma.relation(b)], a),
        ([memory, ma.relation(a), ma.relation(b)], a),
        ([memory, ma.relation(b), ma.relation(a)], b),
    ):
        assert resolver.resolve(ma.concat(inputs)._node).connection is expected._find_backend(use_default=False)
    assert resolver.resolve(ma.concat([memory, memory])._node).binding == "memory"


def test_memory_borrowing_does_not_rebind_unbound_database_table():
    peer = REGISTRY["ibis-duckdb"].build({"id": [1]}, "peer")
    unbound = ibis.table({"id": "int64"}, name="somewhere_else")
    resolver = LocationResolver(IdentityTokens())
    assert resolver.resolve(ma.relation(unbound)._node).binding == "unbound"
    assert resolver.resolve(ma.relation(unbound).join(peer, on="id")._node).binding == "unbound"


def test_mixed_bound_native_ibis_sources_are_not_one_location():
    left = REGISTRY["ibis-duckdb"].build({"id": [1]}, "same")
    right = REGISTRY["ibis-duckdb"].build({"id": [2]}, "same")
    mixed = left.union(right)
    assert LocationResolver(IdentityTokens()).resolve(ma.relation(mixed)._node).binding == "unresolved"


def test_cross_dialect_native_graph_is_not_mistaken_for_one_bound_source():
    left = REGISTRY["ibis-duckdb"].build({"id": [1]}, "left")
    right = REGISTRY["ibis-sqlite"].build({"id": [2]}, "right")
    mixed = left.union(right)
    assert LocationResolver(IdentityTokens()).resolve(ma.relation(mixed)._node).binding == "unresolved"


@pytest.mark.parametrize("backend_name", IBIS_BACKENDS)
def test_resolution_never_materializes_or_opens_an_implicit_backend(monkeypatch, backend_name):
    bound = REGISTRY[backend_name].build({"id": [1]}, "bound")
    memory = ma.relation(ibis.memtable(pa.table({"id": [1]}))).filter(ma.col("id") > 0)

    def forbidden(*args, **kwargs):
        raise AssertionError("resolver evaluated data or opened a default database")

    monkeypatch.setattr(type(bound), "to_pyarrow", forbidden)
    monkeypatch.setattr(type(bound), "cache", forbidden)
    from ibis.expr.types.relations import Table
    original = Table._find_backend

    def no_default(self, *, use_default=True):
        if use_default:
            forbidden()
        return original(self, use_default=False)

    monkeypatch.setattr(Table, "_find_backend", no_default)
    resolver = LocationResolver(IdentityTokens())
    assert resolver.resolve(memory.join(bound, on="id")._node).connection is bound._find_backend(use_default=False)
    assert resolver.resolve(memory._node).binding == "memory"


@pytest.mark.parametrize("backend_name", list(REGISTRY))
def test_native_read_families_and_forms(backend_name):
    value = REGISTRY[backend_name].build({"id": [1]}, "native")
    location = LocationResolver(IdentityTokens()).resolve(ma.relation(value)._node)
    expected = REGISTRY[backend_name]
    assert location.family.value == ("narwhals" if expected.family == "pandas" else expected.family.split("-")[0])
    assert location.form.name.lower() == expected.materialization
    assert location.binding == "bound"


def test_ref_resolution_cycle_missing_and_standalone():
    ref_a, ref_b = RefRelNode(name="a"), RefRelNode(name="b")
    values = {"a": ref_b, "b": ref_a, "data": ma.relation({"id": [1]})._node}
    resolver = LocationResolver(IdentityTokens(), identity_resolver=values.__getitem__)
    assert resolver.resolve(RefRelNode(name="data")).family is CONST_BACKEND.POLARS
    with pytest.raises(UnresolvedExecutionLocationError, match="Cyclic"):
        resolver.resolve(ref_a)
    with pytest.raises(UnknownRelationRef):
        resolver.resolve(RefRelNode(name="missing"))
    with pytest.raises(RelationDAGRequired):
        LocationResolver(IdentityTokens()).resolve(ref_a)


def test_resource_and_registered_extension_location_does_not_execute(monkeypatch):
    from mountainash.pipelines.integration.relation import PipelineStepRelNode
    from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import MountainashPolarsExtensionRelationSystem

    def forbidden(*args, **kwargs):
        raise AssertionError("resolution read data")

    monkeypatch.setattr(MountainashPolarsExtensionRelationSystem, "_read_inline", forbidden)
    resolver = LocationResolver(IdentityTokens())
    resource = ResourceReadRelNode(resource=DataResource(name="source", data=[{"id": 1}]))
    assert resolver.resolve(resource).family is CONST_BACKEND.POLARS
    assert resolver.resolve(PipelineStepRelNode(step_name="step", pipeline=object())).family is CONST_BACKEND.POLARS


def test_error_context_is_safe_and_preserved():
    for cls in (UnresolvedExecutionLocationError, ConflictingExecutionTargetError):
        error = cls("placement failed", node_key="root/right", source="ibis-sqlite",
                    destination="ibis-duckdb")
        assert isinstance(error, ValueError)
        assert (error.node_key, error.source, error.destination) == (
            "root/right", "ibis-sqlite", "ibis-duckdb")
        assert str(error) == "placement failed"


def test_contextual_binding_is_not_written_onto_reused_ast_or_bound_inner_join():
    first = REGISTRY["ibis-duckdb"].build({"id": [1]}, "first")
    second = REGISTRY["ibis-sqlite"].build({"id": [1]}, "second")
    memory = ma.relation(ibis.memtable(pa.table({"id": [1]}))).filter(ma.col("id") > 0)
    inner = ma.relation(first).join(memory, on="id")
    resolver = LocationResolver(IdentityTokens())
    first_location = resolver.resolve(ma.relation(first)._node)
    second_location = resolver.resolve(ma.relation(second)._node)
    assert resolver.resolve(memory._node, binding=first_location).connection is first_location.connection
    assert resolver.resolve(memory._node, binding=second_location).connection is second_location.connection
    assert resolver.resolve(inner._node, binding=second_location).connection is first_location.connection
    assert resolver.resolve(memory._node).binding == "memory"


def test_unknown_leaf_never_steals_the_others_location():
    class UnknownRelNode(RelationNode):
        pass

    bound = REGISTRY["ibis-duckdb"].build({"id": [1]}, "peer")
    unknown = UnknownRelNode()
    resolver = LocationResolver(IdentityTokens())
    assert resolver.resolve(unknown).binding == "unresolved"
    result = JoinRelNode(left=ma.relation(bound)._node, right=unknown,
                         join_type=JoinType.INNER, on=["id"], execute_on=ExecutionTarget.RIGHT)
    assert resolver.resolve(result).family is None
