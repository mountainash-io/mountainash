"""Public DAG outputs remain bound to the entry request's frozen policy."""

import pytest

from mountainash.core.capabilities.applicability import unbounded


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb"])
@pytest.mark.parametrize("terminal", ["collect", "execute"])
def test_dag_freezes_policy_before_named_compilation(backend_name, backend_factory, monkeypatch, terminal):
    import mountainash as ma
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
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK
    from mountainash.relations.dag.materialization import DAGMaterializationSession

    family = CONST_BACKEND(backend_name.split("-")[0])
    before = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(
            BoundSegment(
                f"mountainash.expressions.backends.capabilities.{family.value}.dialects.{backend_name.replace('-', '_')}.substrait.string",
                Scope(family, Dialect(backend_name)),
                CapabilitySegment(
                    Domain.STRING,
                    policies=(
                        CapabilityPolicyRule(
                            CapabilityKey(FK.CONTAINS, "substring"),
                            CapabilityLevel.UNSUPPORTED,
                            "controlled gate",
                            PolicyConsumer.GATE,
                            PolicyAction.BLOCK,
                            applicability=unbounded,
                        ),
                    ),
                ),
            )
        )
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


@pytest.fixture()
def regex_form_policy():
    """Author a local policy; this does not assert any native backend defect."""
    from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
    from mountainash.core.capabilities.declarations import (
        BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector,
    )
    from mountainash.core.capabilities.identity import Dialect, Scope
    from mountainash.core.capabilities.schema import Clause, ClauseOp, PolicyAction, PolicyConsumer, Predicate
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRING as FK

    before = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()

    def install(backend_name, form="is_dynamic"):
        family = CONST_BACKEND(backend_name.split("-")[0])
        predicate = Predicate((
            Clause("pattern", ClauseOp(form)),
            Clause("case_sensitivity", ClauseOp.EQ, "CASE_INSENSITIVE"),
        ))
        CapabilityRegistry.register_segment(BoundSegment(
            f"mountainash.expressions.backends.capabilities.{family.value}.dialects."
            f"{backend_name.replace('-', '_')}.extensions_mountainash.string",
            Scope(family, Dialect(backend_name)),
            CapabilitySegment(Domain.STRING, policies=(CapabilityPolicyRule(
                CapabilityKey(FK.REGEX_CONTAINS, "pattern", Selector("predicate", predicate)),
                CapabilityLevel.UNSUPPORTED, "authored argument-form protection",
                PolicyConsumer.GATE, PolicyAction.BLOCK, applicability=unbounded,
            ),)),
        ))

    try:
        yield install
    finally:
        CapabilityRegistry.restore(before)


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb"])
@pytest.mark.parametrize("shape", ["column", "computed", "computed-constant", "literal"])
def test_dynamic_regex_policy_preserves_literal_neighbor(
    backend_name, shape, backend_factory, collect_expr, regex_form_policy,
):
    import mountainash as ma
    from mountainash.core.types import BackendCapabilityError

    regex_form_policy(backend_name)
    frame = backend_factory.create({"value": ["AU", "au", "NZ", "", None, "AU"],
                                    "pattern": ["^AU$", "^AU$", "^AU$", "^", "^", None]}, backend_name)
    pattern = {
        "column": ma.col("pattern"),
        "computed": ma.col("pattern") + ma.lit("$"),
        "computed-constant": ma.lit("^AU") + ma.lit("$"),
        "literal": ma.lit("^AU$"),
    }[shape]
    expression = ma.col("value").str.regex_contains(pattern, case_sensitive=False)
    if shape == "literal":
        assert collect_expr(frame, expression) == [True, True, False, False, None, True]
    else:
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(frame, expression)
        assert error.value.function_key.name == "REGEX_CONTAINS"


@pytest.mark.parametrize("form", ["is_literal", "is_dynamic"])
@pytest.mark.parametrize("shape", ["column", "computed", "deferred", "literal"])
def test_native_regex_forms_share_one_policy_classification(
    form, shape, backend_factory, collect_expr, regex_form_policy,
):
    """Ibis native values/deferred forms have no equivalent on other providers."""
    import ibis
    import mountainash as ma
    from mountainash.core.types import BackendCapabilityError

    regex_form_policy("ibis-duckdb", form)
    table = backend_factory.create({"value": ["AU", "au", "NZ", "", None, "AU"],
                                    "pattern": ["^AU$", "^AU$", "^AU$", "^", "^", None]}, "ibis-duckdb")
    pattern = {"column": table.pattern, "computed": table.pattern + "$",
               "deferred": ibis._["pattern"], "literal": ibis.literal("^AU$")}[shape]
    expression = ma.col("value").str.regex_contains(ma.native(pattern), case_sensitive=False)
    expected = ([True, True, False, False, None, True] if shape == "literal"
                else [True, True, False, True, None, None])
    if (shape == "literal") == (form == "is_literal"):
        with pytest.raises(BackendCapabilityError) as error:
            collect_expr(table, expression)
        assert error.value.function_key.name == "REGEX_CONTAINS"
    elif shape == "deferred":
        # Native Deferred lowering is unsupported independently of the policy.
        with pytest.raises(TypeError):
            collect_expr(table, expression)
    else:
        assert collect_expr(table, expression) == expected
    with ma.capability_policy(ma.CapabilityPolicy.trusted()):
        if shape == "deferred":
            with pytest.raises(TypeError):
                collect_expr(table, expression)
        else:
            assert collect_expr(table, expression) == expected


def test_unknown_native_regex_retains_ordinary_error(backend_factory, collect_expr, regex_form_policy):
    """Ibis-only native-error boundary, not a cross-backend semantic assertion."""
    import mountainash as ma

    regex_form_policy("ibis-duckdb")
    table = backend_factory.create({"value": ["AU"]}, "ibis-duckdb")
    expression = ma.col("value").str.regex_contains(ma.native(object()), case_sensitive=False)
    for policy in (ma.CapabilityPolicy.checked(), ma.CapabilityPolicy.trusted()):
        with ma.capability_policy(policy), pytest.raises(TypeError):
            collect_expr(table, expression)
