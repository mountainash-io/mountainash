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
        rel.collect(target="polars")


@pytest.mark.parametrize("terminal", ["collect", "collect_with_drift"])
@pytest.mark.parametrize("targeted", [False, True])
def test_unknown_terminal_backend_is_rejected_before_compilation(terminal, targeted):
    left = REGISTRY["polars"].build({"id": [1]}, "left")
    rel = ma.relation(left)
    if targeted:
        right = REGISTRY["ibis-duckdb"].build({"id": [1]}, "right")
        rel = rel.join(right, on="id", execute_on="right")
    with pytest.raises(ValueError, match="unknown target: 'bogus'"):
        getattr(rel, terminal)(target="bogus")


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


def test_shared_transfer_failure_recovers_on_same_recipe():
    import polars as pl

    stored = ma.relation(REGISTRY["ibis-duckdb"].build({"id": [7]}, "stored"))
    payload = {"id": ["bad"]}
    request = ma.relation(payload).select(ma.col("id").cast(ma.MountainashDtype.I64))
    query = ma.concat([stored.join(request, on="id")] * 4)
    for _ in range(2):
        with pytest.raises(pl.exceptions.InvalidOperationError):
            query.to_dicts()
    payload["id"][0] = "7"
    assert query.to_dicts() == [{"id": 7}] * 4
    assert stored.to_dicts() == [{"id": 7}]


@pytest.mark.parametrize("named", [False, True])
def test_lowering_error_survives_owned_cleanup_error(monkeypatch, named):
    from mountainash.relations.core.execution.compilation import CompilationSession
    from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem

    primary = ValueError("native lowering failed")
    released = []
    initialize = CompilationSession.__init__

    def release():
        released.append(True)
        raise RuntimeError("owned cleanup failed")

    def initialize_with_owned_resource(self, *args, **kwargs):
        initialize(self, *args, **kwargs)
        if kwargs.get("transport") is None:
            self.transport._scope.own(release)

    def fail_lowering(*args, **kwargs):
        raise primary

    monkeypatch.setattr(CompilationSession, "__init__", initialize_with_owned_resource)
    monkeypatch.setattr(PolarsRelationSystem, "filter", fail_lowering)
    source = ma.relation({"id": [1]})
    if named:
        dag = ma.RelationDAG()
        dag.add("source", source)
        source = dag.ref("source")
    branch = source.filter(ma.col("id") > 0)
    with pytest.raises(ValueError) as caught:
        ma.concat([branch] * 4).to_dicts()
    assert caught.value is primary
    assert released == [True]


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
    from mountainash.typespec import FieldDefinition, TableSchema, UniversalType

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
                TableSchema(
                    fields_match="open",
                    fields={"year": FieldDefinition(type=UniversalType.YEAR)},
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
            with pytest.raises(BackendCapabilityError) as copy_refusal:
                rel.snapshot()
            if not targeted_join:
                assert isinstance(copy_refusal.value.__cause__, CompileRequiresExecutionError)
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
    from mountainash.typespec import FieldDefinition, TableSchema, UniversalType

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
                TableSchema(
                    fields_match="open",
                    fields={"year": FieldDefinition(type=UniversalType.YEAR)},
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
            second = rel.collect()
            assert ma.relation(second).to_dict() == {"id": [99]}
            assert ma.relation(native).to_dict() == {"id": [1]}
            del second
            gc.collect()
    finally:
        CapabilityRegistry.restore(snapshot)


# --- target= vocabulary: connection-level conflicts (location-centred transfer, Task 2) ---

import polars as pl  # noqa: E402
import pyarrow as pa  # noqa: E402


@pytest.fixture
def two_duck():
    import ibis

    a, b = ibis.duckdb.connect(), ibis.duckdb.connect()
    return a, b, a.create_table("ta", {"id": [1, 2], "x": [1, 2]}), b.create_table("tb", {"id": [1, 2], "y": [3, 4]})


def _right(ta, tb):
    return ma.relation(ta).join(ma.relation(tb), on="id", execute_on="right")


def test_family_target_keeps_selected_connection(two_duck):
    a, b, ta, tb = two_duck
    assert _right(ta, tb).collect(target="ibis").get_backend() is b


def test_same_connection_target_is_compatible(two_duck):
    a, b, ta, tb = two_duck
    assert _right(ta, tb).collect(target=b).get_backend() is b


@pytest.mark.parametrize("pick", [lambda a, b: a, lambda a, b: "ibis-sqlite"], ids=["connection", "dialect"])
def test_conflicting_target(two_duck, pick):
    a, b, ta, tb = two_duck
    with pytest.raises(ConflictingExecutionTargetError):
        _right(ta, tb).collect(target=pick(a, b))


def test_removed_keywords_are_rejected():
    rel = ma.relation(pl.DataFrame({"a": [1]}))
    with pytest.raises(TypeError):
        rel.collect(backend="polars")
    with pytest.raises(TypeError):
        rel.compile(target="polars")
    with pytest.raises(TypeError):
        ma.from_arrow(pa.table({"a": [1]}), connection=None)


def test_dag_ref_default_collect():
    dag = ma.RelationDAG()
    dag.add("t", ma.relation(pl.DataFrame({"a": [1]})))
    assert dag.ref("t").collect().to_dicts() == [{"a": 1}]
