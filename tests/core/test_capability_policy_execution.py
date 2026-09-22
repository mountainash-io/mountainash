"""Public DAG outputs remain bound to the entry request's frozen policy."""
import pytest


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb"])
@pytest.mark.parametrize("terminal", ["collect", "execute"])
def test_dag_freezes_policy_before_named_compilation(backend_name, backend_factory, monkeypatch, terminal):
    import mountainash as ma
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.types import BackendCapabilityError
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK
    from mountainash.relations.dag.materialization import DAGMaterializationSession
    family = CONST_BACKEND(backend_name.split("-")[0])
    before = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(BoundSegment(
            f"mountainash.expressions.backends.capabilities.{family.value}.dialects.{backend_name.replace('-', '_')}.substrait.string",
            Scope(family, Dialect(backend_name)),
            CapabilitySegment(Domain.STRING, policies=(CapabilityPolicyRule(
                CapabilityKey(FK.CONTAINS, "substring"), CapabilityLevel.UNSUPPORTED,
                "2026-09-21", "controlled gate", PolicyConsumer.GATE, PolicyAction.BLOCK,
            ),)),
        ))
        dag = ma.RelationDAG()
        dag.add("source", ma.relation(backend_factory.create({"text": ["a", "b"]}, backend_name)))
        pipeline = dag.ref("source").select(ma.col("text").str.contains("a").alias("found"))
        dag.add("result", pipeline)
        run = (lambda: dag.collect("result")) if terminal == "collect" else (lambda: dag.execute(pipeline))
        original = DAGMaterializationSession._compile_named
        def enter_debug_scope(self, *args, **kwargs):
            with ma.capability_policy(ma.CapabilityPolicy.trusted()):
                return original(self, *args, **kwargs)
        monkeypatch.setattr(DAGMaterializationSession, "_compile_named", enter_debug_scope)
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            with pytest.raises(BackendCapabilityError):
                run()
        with ma.capability_policy(ma.CapabilityPolicy.trusted()):
            native = run()
            assert ma.relation(native).to_polars()["found"].to_list() == [True, False]
    finally:
        CapabilityRegistry.restore(before)
