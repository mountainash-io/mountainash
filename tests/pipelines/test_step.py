from mountainash.pipelines.core.step import step, StepContext, StepDefinition
from mountainash.pipelines.core.capabilities import (
    StepCapabilities,
    PushableParam,
    ResolvedPredicates,
)
from mountainash.pipelines.core.policies import EmptyPolicy
from datetime import timedelta, datetime


def test_step_decorator_basic():
    @step(name="my_step")
    def my_step(ctx: StepContext) -> list[dict]:
        return [{"a": 1}]

    assert hasattr(my_step, "_step_definition")
    defn = my_step._step_definition
    assert isinstance(defn, StepDefinition)
    assert defn.name == "my_step"
    assert defn.depends_on == []
    assert defn.capabilities == StepCapabilities()
    assert defn.empty_policy == EmptyPolicy.WARN


def test_step_decorator_with_deps():
    @step(name="child", depends_on=["parent1", "parent2"])
    def child(ctx: StepContext, parent1: list, parent2: list) -> list:
        return parent1 + parent2

    defn = child._step_definition
    assert defn.depends_on == ["parent1", "parent2"]


def test_step_decorator_with_capabilities():
    @step(
        name="extract",
        pushdown=StepCapabilities(
            pushable_params=(PushableParam(column="date", api_param="start"),),
        ),
        cache_ttl=timedelta(hours=1),
        empty_policy=EmptyPolicy.FAIL,
    )
    def extract(ctx: StepContext) -> list[dict]:
        return []

    defn = extract._step_definition
    assert defn.capabilities.pushable_params[0].column == "date"
    assert defn.cache_ttl == timedelta(hours=1)
    assert defn.empty_policy == EmptyPolicy.FAIL


def test_step_function_remains_callable():
    @step(name="my_step")
    def my_step(ctx: StepContext) -> list[dict]:
        return [{"result": True}]

    ctx = StepContext(
        predicates=ResolvedPredicates(resolution_timestamp=datetime.now()),
        pipeline_storage=None,
        storage_facade=None,
        config={},
        step_name="my_step",
        workflow_id=None,
    )
    result = my_step(ctx)
    assert result == [{"result": True}]


def test_step_context_fields():
    ctx = StepContext(
        predicates=ResolvedPredicates(resolution_timestamp=datetime.now()),
        pipeline_storage=None,
        storage_facade=None,
        config={"key": "value"},
        step_name="test",
        workflow_id="wf-123",
    )
    assert ctx.step_name == "test"
    assert ctx.workflow_id == "wf-123"
    assert ctx.config["key"] == "value"
