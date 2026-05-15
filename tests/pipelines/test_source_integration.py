import polars as pl
from mountainash.pipelines import source, pipeline
from mountainash.pipelines.core.step import step, StepContext
from mountainash.pipelines.storage.memory import MemoryPipelineStorage
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner


@step(name="fetch")
def fetch(ctx: StepContext) -> list[dict]:
    return [{"id": 1, "value": 42}]


class InlineExecutor:
    def __init__(self, spec, storage):
        self._runner = SimplePipelineRunner(spec=spec, storage=storage)

    def execute(self, pipeline, step_name, predicates, data_key=None):
        results = self._runner.run()
        result = results[step_name]
        data = result.data
        if data_key is not None:
            data = data[data_key]
        return pl.DataFrame(data).lazy()


def test_source_produces_collectible_relation():
    spec = pipeline("test", version="1.0.0").step("fetch", fetch).build()
    storage = MemoryPipelineStorage()
    executor = InlineExecutor(spec=spec, storage=storage)

    rel = source("fetch", pipeline=spec, executor=executor)

    result = rel.collect()
    assert isinstance(result, pl.DataFrame)
    assert result.shape == (1, 2)
    assert result["value"][0] == 42


def test_source_returns_relation_type():
    from mountainash.relations.core.relation_api.relation import Relation
    spec = pipeline("test", version="1.0.0").step("fetch", fetch).build()
    storage = MemoryPipelineStorage()
    executor = InlineExecutor(spec=spec, storage=storage)

    rel = source("fetch", pipeline=spec, executor=executor)
    assert isinstance(rel, Relation)
