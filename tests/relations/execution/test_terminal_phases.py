"""Phase routing at public terminals."""

import pytest
from fixtures.backend_registry import REGISTRY

import mountainash as ma
from mountainash.core.capabilities.applicability import unbounded
from mountainash.relations.core.errors import CompileRequiresExecutionError, ConflictingExecutionTargetError


def test_compile_rejects_cross_connection_before_export(monkeypatch):
    left = REGISTRY["ibis-duckdb"].build({"id": [1]}, "left")
    right = REGISTRY["ibis-sqlite"].build({"id": [1]}, "right")
    rel = ma.relation(left).join(right, on="id", execute_on="right")

    def forbidden(*args, **kwargs):
        raise AssertionError("compile/explain exported rows")

    monkeypatch.setattr(type(left), "to_pyarrow", forbidden)
    with pytest.raises(CompileRequiresExecutionError, match="collect"):
        rel.compile()
    text = rel.explain()
    assert "ibis-duckdb" in text and "ibis-sqlite" in text
    assert "transfer" in text


def test_nested_target_conflicting_backend_is_rejected():
    left = REGISTRY["polars"].build({"id": [1]}, "a")
    right = REGISTRY["ibis-duckdb"].build({"id": [1]}, "b")
    rel = ma.relation(left).join(right, on="id", execute_on="right")
    with pytest.raises(ConflictingExecutionTargetError):
        rel.collect(backend="polars")


@pytest.mark.parametrize("terminal", ["collect", "collect_with_drift"])
@pytest.mark.parametrize("targeted", [False, True])
def test_unknown_terminal_backend_is_rejected_before_compilation(terminal, targeted):
    left = REGISTRY["polars"].build({"id": [1]}, "left")
    rel = ma.relation(left)
    if targeted:
        right = REGISTRY["ibis-duckdb"].build({"id": [1]}, "right")
        rel = rel.join(right, on="id", execute_on="right")
    with pytest.raises(ValueError, match="unknown backend: 'bogus'"):
        getattr(rel, terminal)(backend="bogus")


def test_failed_native_terminal_releases_execution_scope(monkeypatch):
    from mountainash.relations.core import materialization
    from mountainash.relations.core.execution.transport import TransportSession

    frame = REGISTRY["polars"].build({"id": [1]}, "source")
    closed = []
    original_close = TransportSession.close

    def recorded_close(self, *, release_owned):
        closed.append(release_owned)
        return original_close(self, release_owned=release_owned)

    def broken(*args, **kwargs):
        raise RuntimeError("terminal failed")

    monkeypatch.setattr(TransportSession, "close", recorded_close)
    monkeypatch.setattr(materialization, "materialize_native", broken)
    with pytest.raises(RuntimeError, match="terminal failed"):
        ma.relation(frame).collect()
    assert closed == [True]


@pytest.mark.parametrize("year,raises", [("2024", False), ("not-a-year", True)])
@pytest.mark.parametrize("targeted_join", [False, True])
def test_source_marker_is_checked_before_projection_drops_it(year, raises, targeted_join, monkeypatch):
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityKey,
        CapabilityPolicyRule,
        CapabilitySegment,
        Domain,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.types import BackendCapabilityError
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_DATETIME as FK,
    )
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(
            BoundSegment(
                "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.extensions_mountainash.datetime",
                Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
                CapabilitySegment(
                    Domain.DATETIME,
                    policies=(
                        CapabilityPolicyRule(
                            key=CapabilityKey(FK.PARSE_XSD_PARTIAL_DATE, "*"),
                            level=CapabilityLevel.UNSUPPORTED,
                            message="source year residue",
                            consumer=PolicyConsumer.RESULT_PROTECTION,
                            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
                            applicability=unbounded,
                        ),
                    ),
                ),
            )
        )
        frame = REGISTRY["ibis-duckdb"].build({"id": [1], "year": [year]}, "source")
        rel = (
            ma.relation(frame)
            .conform(
                TypeSpec(
                    fields_match="open",
                    fields=[FieldSpec(name="year", type=UniversalType.YEAR)],
                )
            )
            .select("id")
        )
        if targeted_join:
            peer = REGISTRY["ibis-sqlite"].build({"id": [1]}, "peer")
            rel = rel.join(peer, on="id", execute_on="right")
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            original_export = type(frame).to_pyarrow

            def forbidden(*args, **kwargs):
                raise AssertionError("compile executed a source residue check")

            monkeypatch.setattr(type(frame), "to_pyarrow", forbidden)
            with pytest.raises(CompileRequiresExecutionError, match="collect"):
                rel.compile()
            monkeypatch.setattr(type(frame), "to_pyarrow", original_export)
            if raises:
                with pytest.raises(BackendCapabilityError) as caught:
                    rel.collect()
                assert caught.value.backend == "ibis"
                assert caught.value.limitation.dialect == "ibis-duckdb"
            else:
                assert ma.relation(rel.collect()).to_dict() == {"id": [1]}
    finally:
        CapabilityRegistry.restore(snapshot)


def test_checked_projection_returns_the_checked_source_snapshot():
    import gc

    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityKey,
        CapabilityPolicyRule,
        CapabilitySegment,
        Domain,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_DATETIME as FK,
    )
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(
            BoundSegment(
                "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.extensions_mountainash.datetime",
                Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
                CapabilitySegment(
                    Domain.DATETIME,
                    policies=(
                        CapabilityPolicyRule(
                            key=CapabilityKey(FK.PARSE_XSD_PARTIAL_DATE, "*"),
                            level=CapabilityLevel.UNSUPPORTED,
                            message="source year residue",
                            consumer=PolicyConsumer.RESULT_PROTECTION,
                            action=PolicyAction.DETECT_NON_NULL_TO_NULL,
                            applicability=unbounded,
                        ),
                    ),
                ),
            )
        )
        source = REGISTRY["ibis-duckdb"].build({"id": [1], "year": ["2024"]}, "snapshot_source")
        connection = source._find_backend(use_default=False)
        rel = (
            ma.relation(source)
            .conform(
                TypeSpec(
                    fields_match="open",
                    fields=[FieldSpec(name="year", type=UniversalType.YEAR)],
                )
            )
            .select("id")
        )
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            native = rel.collect()
            gc.collect()
            connection.create_table(
                "snapshot_source",
                {"id": [99], "year": ["2025"]},
                overwrite=True,
            )
            assert ma.relation(native).to_dict() == {"id": [1]}
            before = set(connection.list_tables())
            assert set(rel.to_polars().columns) == {"id"}
            gc.collect()
            assert set(connection.list_tables()) == before
    finally:
        CapabilityRegistry.restore(snapshot)
