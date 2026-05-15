from mountainash.relations.core.relation_api.relation import Relation
from mountainash.pipelines.fluent.source import source
from mountainash.pipelines.fluent.builder import pipeline
from mountainash.pipelines.core.step import step, StepContext
from mountainash.pipelines.integration.relation import PipelineStepRelNode


@step(name="fetch")
def fetch(ctx: StepContext) -> list[dict]:
    return [{"id": 1}]


def test_source_creates_relation():
    spec = pipeline("test", version="1.0.0").step("fetch", fetch).build()
    rel = source("fetch", pipeline=spec, data_key="items")
    assert rel is not None
    assert isinstance(rel, Relation)


def test_source_creates_pipeline_step_rel_node():
    spec = pipeline("test", version="1.0.0").step("fetch", fetch).build()
    rel = source("fetch", pipeline=spec)
    assert hasattr(rel, "_node")
    node = rel._node
    assert isinstance(node, PipelineStepRelNode)
    assert node.step_name == "fetch"
    assert node.pipeline is spec


def test_source_with_data_key():
    spec = pipeline("test", version="1.0.0").step("fetch", fetch).build()
    rel = source("fetch", pipeline=spec, data_key="sleep")
    assert rel._node.data_key == "sleep"
