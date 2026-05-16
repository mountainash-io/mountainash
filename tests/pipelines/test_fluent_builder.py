import pytest
from mountainash.pipelines.fluent.builder import pipeline
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import step, StepContext
from mountainash.pipelines.core.capabilities import StepCapabilities, PushableParam


def _noop(ctx: StepContext) -> list[dict]:
    return []


def test_pipeline_builder_basic():
    spec = (
        pipeline("test", version="1.0.0")
        .step("a", _noop)
        .step("b", _noop, depends_on=["a"])
        .build()
    )
    assert isinstance(spec, PipelineSpec)
    assert spec.name == "test"
    assert spec.version == "1.0.0"
    assert "a" in spec.steps
    assert "b" in spec.steps
    assert spec.steps["b"].depends_on == ["a"]


def test_pipeline_builder_with_capabilities():
    spec = (
        pipeline("test", version="2.0.0")
        .step("extract", _noop, pushdown=StepCapabilities(
            pushable_params=(PushableParam(column="date", api_param="start"),),
        ))
        .build()
    )
    assert spec.steps["extract"].capabilities.pushable_params[0].column == "date"


def test_pipeline_builder_with_decorated_steps():
    @step(name="src")
    def src(ctx: StepContext) -> list[dict]:
        return [{"x": 1}]

    @step(name="transform", depends_on=["src"])
    def transform(ctx: StepContext, src: list[dict]) -> list[dict]:
        return src

    spec = (
        pipeline("test", version="1.0.0")
        .step("src", src)
        .step("transform", transform, depends_on=["src"])
        .build()
    )
    assert spec.steps["src"].fn is not None
    assert spec.steps["transform"].depends_on == ["src"]


def test_pipeline_builder_returns_new_builder():
    b1 = pipeline("test", version="1.0.0")
    b2 = b1.step("a", _noop)
    assert b1 is not b2


def test_pipeline_builder_duplicate_name_raises():
    with pytest.raises(ValueError, match="already exists"):
        pipeline("test", version="1.0.0").step("a", _noop).step("a", _noop).build()
