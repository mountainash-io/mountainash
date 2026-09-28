"""Real native transfers and execution-local ownership boundaries."""

from __future__ import annotations

import gc
from dataclasses import replace

import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.core.transit import BoundaryKey, capture_conversion_trace
from mountainash.relations.core.errors import UnsupportedRelationTransportError
from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
from mountainash.relations.core.execution.metadata import CompiledSubtree, CompilationMetadata
from mountainash.relations.core.execution.preparation import TransferRequirement
from mountainash.relations.core.execution.transport import TransportSession
from mountainash.relations.core.materialization import MaterializationScope


IBIS_BACKENDS = [name for name, spec in REGISTRY.items() if spec.family == "ibis"]


def test_bare_ibis_memory_payload_export_is_a_declared_arrow_boundary():
    import ibis
    import polars as pl

    memory = ibis.memtable({"id": [1], "value": ["kept"]})
    with capture_conversion_trace() as trace:
        rows = ma.relation(pl.DataFrame({"id": [1]})).join(memory, on="id").to_dicts()
    assert rows == [{"id": 1, "value": "kept"}]
    assert BoundaryKey.IBIS_MEMORY_PAYLOAD_TO_ARROW in {
        record.boundary_key for record in trace.records
    }


def test_sqlite_storage_preflight_exports_native_frames_through_declared_arrow_boundary():
    import ibis
    import polars as pl

    destination = ibis.sqlite.connect(":memory:").create_table("destination", {"id": [1]})
    source = pl.DataFrame({"id": [1], "value": [float("nan")]})
    with capture_conversion_trace() as trace:
        with pytest.raises(UnsupportedRelationTransportError):
            ma.relation(source).join(destination, on="id", execute_on="right").collect()
    assert BoundaryKey.STORAGE_PREFLIGHT_TO_ARROW in {
        record.boundary_key for record in trace.records
    }


@pytest.mark.parametrize("source_name", IBIS_BACKENDS)
@pytest.mark.parametrize("destination_name", IBIS_BACKENDS)
def test_derived_sources_have_separate_cached_transfers(source_name, destination_name, monkeypatch):
    import mountainash.relations.core.execution.transport as transport

    table = REGISTRY[source_name].build({"id": [1, 2]}, "same")
    target = REGISTRY[destination_name].build({"id": [1, 2]}, "same")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    source_location = resolver.resolve(ma.relation(table)._node)
    destination = resolver.resolve(ma.relation(target)._node)
    boundaries = []
    original = transport.transit_call

    def spy(key, *args, **kwargs):
        boundaries.append(key)
        return original(key, *args, **kwargs)

    monkeypatch.setattr(transport, "transit_call", spy)
    session = TransportSession(tokens)
    try:
        for selected in (1, 2):
            value = table.filter(table.id == selected)
            source = CompiledSubtree(value, source_location, tokens.token(value), CompilationMetadata())
            requirement = TransferRequirement(str(selected), destination, "ibis_arrow_ibis", True)
            first = session.transfer(source, requirement)
            assert session.transfer(source, requirement) is first
            assert first.location is destination
            joined = target.inner_join(first.value, "id").select(target.id)
            assert joined._find_backend(use_default=False) is target._find_backend(use_default=False)
            assert ma.relation(joined).to_dict() == {"id": [selected]}
        assert boundaries.count(BoundaryKey.IBIS_TO_ARROW_EGRESS) == 2
        assert boundaries.count(BoundaryKey.ARROW_TO_IBIS_ADAPTER) == 2
        another = REGISTRY[destination_name].build({"id": [1, 2]}, "another")
        other_destination = resolver.resolve(ma.relation(another)._node)
        other = session.transfer(source, replace(requirement, destination=other_destination))
        assert other is not first
        assert other.location.key != first.location.key
    finally:
        session.close(release_owned=True)


def test_cache_is_per_session_and_failed_adapter_does_not_cache(monkeypatch):
    import mountainash.relations.core.execution.transport as transport
    from mountainash.relations.core.errors import UnsupportedRelationTransportError

    source_table = REGISTRY["ibis-duckdb"].build({"id": [1]}, "src")
    target = REGISTRY["ibis-sqlite"].build({"id": [1]}, "dst")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    value = source_table.filter(source_table.id == 1)
    source = CompiledSubtree(value, resolver.resolve(ma.relation(source_table)._node),
                             tokens.token(value), CompilationMetadata())
    requirement = TransferRequirement("root/right", resolver.resolve(ma.relation(target)._node),
                                      "ibis_arrow_ibis", True)
    session = TransportSession(tokens)
    original = transport.transit_call

    def broken(key, *args, **kwargs):
        if key is BoundaryKey.ARROW_TO_IBIS_ADAPTER:
            raise ValueError("adapter failed")
        return original(key, *args, **kwargs)

    monkeypatch.setattr(transport, "transit_call", broken)
    with pytest.raises(UnsupportedRelationTransportError) as raised:
        session.transfer(source, requirement)
    assert isinstance(raised.value.__cause__, ValueError)
    assert str(raised.value.__cause__) == "adapter failed"
    assert raised.value.source_dialect == "ibis-duckdb"
    assert raised.value.destination_dialect == "ibis-sqlite"
    assert "adapter failed" not in str(raised.value)
    assert not session._cache
    monkeypatch.setattr(transport, "transit_call", original)
    fresh = TransportSession(tokens)
    first = fresh.transfer(source, requirement)
    second = TransportSession(tokens)
    assert second.transfer(source, requirement) is not first
    fresh.close(release_owned=False)
    second.close(release_owned=True)
    gc.collect()
    joined = target.inner_join(first.value, "id").select(target.id)
    assert ma.relation(joined).to_dict() == {"id": [1]}


def test_lossy_sqlite_route_rolls_back_owned_resources_without_touching_caller(monkeypatch):
    import polars as pl

    from mountainash.relations.core.errors import UnsupportedRelationTransportError

    source_frame = pl.DataFrame({"id": [1], "measure": [float("nan")]})
    target = REGISTRY["ibis-sqlite"].build({"id": [1]}, "target")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    source = CompiledSubtree(
        source_frame, resolver.resolve(ma.relation(source_frame)._node),
        tokens.token(source_frame), CompilationMetadata(),
    )
    requirement = TransferRequirement(
        "root/left", resolver.resolve(ma.relation(target)._node), "polars_to_ibis", True,
    )
    released = []
    caller_released = []
    monkeypatch.setattr(type(target), "release", lambda *_: caller_released.append("table"), raising=False)
    monkeypatch.setattr(type(target._find_backend(use_default=False)), "disconnect",
                        lambda *_: caller_released.append("connection"))
    session = TransportSession(tokens)
    session._scope.own(lambda: released.append("owned"))
    with pytest.raises(UnsupportedRelationTransportError) as caught:
        session.transfer(source, requirement)
    assert caught.value.__cause__ is not None
    assert "NaN" in str(caught.value.__cause__)
    assert released == ["owned"]
    assert caller_released == []
    assert not session._cache
    session.close(release_owned=True)
    assert released == ["owned"]


def test_source_export_enriches_diagnostic_failure_without_owned_checks():
    from mountainash.conform.diagnostics import OperationDiagnostic
    from mountainash.conform.errors import ConformTransformError
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_CAST

    table = REGISTRY["ibis-duckdb"].build({"id": [1], "raw": ["not-an-integer"]}, "src")
    target = REGISTRY["polars"].build({"id": [1]}, "dst")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    value = table.mutate(number=table.raw.cast("int64"))
    diagnostic = OperationDiagnostic(FKEY_SUBSTRAIT_CAST.CAST, "ibis", "ibis-duckdb",
                                     "source-conform", (), "throw", "number", "integer", "default")
    source = CompiledSubtree(value, resolver.resolve(ma.relation(table)._node), tokens.token(value),
                             CompilationMetadata(diagnostic_records=(diagnostic,)))
    destination = resolver.resolve(ma.relation(target)._node)
    requirement = TransferRequirement("root/right", destination, "ibis_to_polars", True)
    with pytest.raises(ConformTransformError) as caught:
        TransportSession(tokens).transfer(source, requirement)
    assert caught.value.__cause__ is not None
    assert caught.value.candidates == (diagnostic,)


@pytest.mark.parametrize("source_name", IBIS_BACKENDS)
@pytest.mark.parametrize("destination_name", IBIS_BACKENDS)
def test_arrow_route_does_not_use_python_data_pandas_or_polars(source_name, destination_name, monkeypatch):
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress

    table = REGISTRY[source_name].build({"id": [1, 2]}, "src")
    target = REGISTRY[destination_name].build({"id": [2]}, "dst")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    source = CompiledSubtree(table.filter(table.id == 2),
                             resolver.resolve(ma.relation(table)._node), tokens.token(object()),
                             CompilationMetadata())
    requirement = TransferRequirement("root/right", resolver.resolve(ma.relation(target)._node),
                                      "ibis_arrow_ibis", True)

    def forbidden(*args, **kwargs):
        raise AssertionError("Ibis-to-Ibis transport must remain Arrow-only")

    with monkeypatch.context() as guard:
        guard.setattr(PydataIngress, "convert", forbidden)
        guard.setattr(type(table), "to_pandas", forbidden)
        guard.setattr(type(table), "to_polars", forbidden, raising=False)
        with TransportSession(tokens) as session:
            moved = session.transfer(source, requirement)
    joined = target.inner_join(moved.value, "id").select(target.id)
    assert joined._find_backend(use_default=False) is target._find_backend(use_default=False)
    assert ma.relation(joined).to_dict() == {"id": [2]}


def test_failed_source_and_destination_cleanup_never_releases_caller_resources(monkeypatch):
    import mountainash.relations.core.execution.transport as transport

    table = REGISTRY["ibis-duckdb"].build({"id": [1]}, "src")
    target = REGISTRY["ibis-sqlite"].build({"id": [1]}, "dst")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    source = CompiledSubtree(table, resolver.resolve(ma.relation(table)._node),
                             tokens.token(table), CompilationMetadata())
    requirement = TransferRequirement("root/right", resolver.resolve(ma.relation(target)._node),
                                      "ibis_arrow_ibis", True)
    released = []
    caller_released = []
    monkeypatch.setattr(type(table), "release", lambda *_: caller_released.append("table"), raising=False)
    monkeypatch.setattr(type(table._find_backend(use_default=False)), "disconnect",
                        lambda *_: caller_released.append("connection"), raising=False)
    original = transport.transit_call

    def fail_export(key, *args, **kwargs):
        if key is BoundaryKey.IBIS_TO_ARROW_EGRESS:
            raise ValueError("source failed")
        return original(key, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(transport, "transit_call", fail_export)
        failed = TransportSession(tokens)
        failed._scope.own(lambda: released.append("export failure"))
        with pytest.raises(ValueError, match="source failed"):
            failed.transfer(source, requirement)
        assert not failed._cache

    with pytest.raises(ValueError, match="consumer failed"):
        with TransportSession(tokens) as session:
            session._scope.own(lambda: released.append("consumer failure"))
            session.transfer(source, requirement)
            raise ValueError("consumer failed")
    assert released == ["export failure", "consumer failure"]
    assert not caller_released
    with TransportSession(tokens) as fresh:
        moved = fresh.transfer(source, requirement)
        assert ma.relation(target.inner_join(moved.value, "id").select(target.id)).to_dict() == {"id": [1]}


@pytest.mark.parametrize("destination_name", IBIS_BACKENDS)
def test_bare_memory_payload_uses_arrow_without_evaluating_table(destination_name, monkeypatch):
    import ibis
    import pyarrow as pa

    memory = ibis.memtable(pa.table({"id": [1, 2]}))
    target = REGISTRY[destination_name].build({"id": [2]}, "dst")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    source = CompiledSubtree(memory, resolver.resolve(ma.relation(memory)._node),
                             tokens.token(memory), CompilationMetadata())
    requirement = TransferRequirement("root/right", resolver.resolve(ma.relation(target)._node),
                                      "ibis_memory_ibis", False)

    def forbidden(*args, **kwargs):
        raise AssertionError("a bare memory payload must not execute an Ibis query")

    with monkeypatch.context() as guard:
        guard.setattr(type(memory), "to_pyarrow", forbidden)
        with TransportSession(tokens) as session:
            moved = session.transfer(source, requirement)
    assert ma.relation(target.inner_join(moved.value, "id").select(target.id)).to_dict() == {"id": [2]}


@pytest.mark.parametrize("destination_name", IBIS_BACKENDS)
def test_derived_polars_plan_is_collected_before_ibis_ingress(destination_name):
    import polars as pl

    table = REGISTRY["polars"].build({"id": [1, 2]}, "src")
    target = REGISTRY[destination_name].build({"id": [2]}, "dst")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    source = CompiledSubtree(table.lazy().filter(pl.col("id") == 2),
                             resolver.resolve(ma.relation(table)._node), tokens.token(object()),
                             CompilationMetadata())
    requirement = TransferRequirement("root/right", resolver.resolve(ma.relation(target)._node),
                                      "polars_to_ibis", True)
    with TransportSession(tokens) as session:
        moved = session.transfer(source, requirement)
    assert ma.relation(target.inner_join(moved.value, "id").select(target.id)).to_dict() == {"id": [2]}


def test_foreign_owned_check_cannot_be_discarded_by_transfer():
    from mountainash.conform.expressions import MaterializationResidueCheck
    from mountainash.relations.core.errors import UnsupportedRelationTransportError
    from mountainash.relations.core.execution.metadata import OwnedResidue

    table = REGISTRY["ibis-duckdb"].build({"id": [1]}, "src")
    target = REGISTRY["ibis-sqlite"].build({"id": [1]}, "dst")
    tokens = IdentityTokens()
    resolver = LocationResolver(tokens)
    source_location = resolver.resolve(ma.relation(table)._node)
    destination = resolver.resolve(ma.relation(target)._node)
    check = OwnedResidue(MaterializationResidueCheck(None, "id", "marker"), "root/source",
                         destination)
    source = CompiledSubtree(table, source_location, tokens.token(table),
                             CompilationMetadata(owned_checks=(check,)))
    requirement = TransferRequirement("root/right", destination, "ibis_arrow_ibis", True)
    with pytest.raises(RuntimeError, match="source boundary"):
        TransportSession(tokens).transfer(source, requirement)
    with pytest.raises(UnsupportedRelationTransportError) as caught:
        TransportSession(tokens).transfer(replace(source, metadata=CompilationMetadata()),
                                          replace(requirement, route="not_declared"))
    assert caught.value.source_dialect == "ibis-duckdb"
    assert caught.value.destination_dialect == "ibis-sqlite"


def test_scope_handoff_and_failure_cleanup_are_isolated():
    calls = []
    scope = MaterializationScope()
    owner = object()
    scope.own(lambda: calls.append("dependency"), owner=owner)
    scope.own(lambda: calls.append("other"))
    scope.handoff((owner,))
    scope.close()
    assert calls == ["other"]
    failed = MaterializationScope()
    failed.own(lambda: calls.append("last"))

    def broken():
        calls.append("broken")
        raise ValueError("cleanup")

    failed.own(broken)
    with pytest.raises(ValueError, match="cleanup"):
        failed.close()
    failed.close()
    assert calls == ["other", "broken", "last"]

    with pytest.raises(RuntimeError, match="primary") as caught:
        with MaterializationScope() as scoped:
            scoped.own(lambda: (_ for _ in ()).throw(ValueError("cleanup")))
            raise RuntimeError("primary")
    assert "Owned-resource cleanup also failed: ValueError" in caught.value.__notes__


@pytest.mark.parametrize("source_name", ["ibis-duckdb", "ibis-polars"])
@pytest.mark.parametrize("year", ["2024", "invalid"])
def test_source_residue_is_checked_before_arrow_export_and_never_leaks(
    source_name, year, backend_factory,
):
    from mountainash.conform.diagnostics import OperationDiagnosticTrace
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.declarations import (
        BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.types import BackendCapabilityError
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_DATETIME as FK,
    )
    from mountainash.relations.core.execution.metadata import MetadataSession
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            f"mountainash.expressions.backends.capabilities.ibis.dialects.{source_name.replace('-', '_')}.extensions_mountainash.datetime",
            Scope(CONST_BACKEND.IBIS, Dialect(source_name)),
            CapabilitySegment(Domain.DATETIME, policies=(CapabilityPolicyRule(
                key=CapabilityKey(FK.PARSE_XSD_PARTIAL_DATE, "*"),
                level=CapabilityLevel.UNSUPPORTED, since="2026-09-27",
                message="Source lexical residue", consumer=PolicyConsumer.RESULT_PROTECTION,
                action=PolicyAction.DETECT_NON_NULL_TO_NULL,
            ),)),
        ))
        table = backend_factory.create({"id": [1], "year": [year]}, source_name)
        target = backend_factory.create({"id": [1]}, "ibis-sqlite")
        spec = TypeSpec(fields_match="open", fields=[FieldSpec(name="year", type=UniversalType.YEAR)])
        rel = ma.relation(table).conform(spec)
        with ma.capability_policy(ma.CapabilityPolicy.checked()) as policy:
            native, visitor = rel._compile_and_execute_with_visitor()
            tokens = IdentityTokens()
            location = LocationResolver(tokens).resolve(ma.relation(table)._node)
            destination = LocationResolver(tokens).resolve(ma.relation(target)._node)
            source = MetadataSession(tokens).capture(visitor, owner_key="root/right",
                                                     location=location, value=native)
            assert source.metadata.owned_checks
            assert source.metadata.diagnostic_records
            session = TransportSession(tokens, execution_context=visitor.execution_context)
            requirement = TransferRequirement("root/right", destination, "ibis_arrow_ibis", True)
            if year == "invalid":
                with pytest.raises(BackendCapabilityError, match="Source lexical residue") as caught:
                    session.transfer(source, requirement)
                assert caught.value.context["field_name"] == "year"
                assert caught.value.limitation.dialect == source_name
                assert not session._cache
            else:
                moved = session.transfer(source, requirement)
                assert moved.metadata.owned_checks == ()
                assert moved.metadata.diagnostic_records is source.metadata.diagnostic_records
                result = target.inner_join(moved.value, "id")
                assert result._find_backend(use_default=False) is target._find_backend(use_default=False)
                assert not any(name.startswith("__ma_residue_") for name in result.columns)
                assert ma.relation(result).to_dict()["id"] == [1]
            session.close(release_owned=True)
    finally:
        CapabilityRegistry.restore(snapshot)
