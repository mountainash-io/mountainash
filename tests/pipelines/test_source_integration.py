"""Integration tests: source() -> Relation -> collect() end-to-end."""
import polars as pl

import mountainash as ma
from mountainash.pipelines import source, PipelineBuilder
from mountainash.pipelines.core.step import step, StepContext
from mountainash.pipelines.storage.memory import MemoryPipelineStorage
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner


@step(name="fetch")
def fetch(ctx: StepContext) -> list[dict]:
    return [{"id": 1, "value": 42}]


def _make_runner(*steps):
    builder = PipelineBuilder("test", version="1.0.0")
    for s in steps:
        builder = builder.step(s._step_definition.name, s)
    spec = builder.build()
    storage = MemoryPipelineStorage()
    return SimplePipelineRunner(spec=spec, storage=storage), spec


class TestSourceCollect:
    def test_source_produces_collectible_relation(self):
        runner, spec = _make_runner(fetch)
        rel = source("fetch", pipeline=spec, executor=runner.as_executor())
        result = rel.collect()
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (1, 2)
        assert result["value"][0] == 42

    def test_source_returns_relation_type(self):
        from mountainash.relations.core.relation_api.relation import Relation

        runner, spec = _make_runner(fetch)
        rel = source("fetch", pipeline=spec, executor=runner.as_executor())
        assert isinstance(rel, Relation)

    def test_chained_operations(self):
        runner, spec = _make_runner(fetch)
        rel = source("fetch", pipeline=spec, executor=runner.as_executor())
        result = (
            rel.with_columns(ma.col("value").mul(2).alias("doubled"))
            .collect()
        )
        assert isinstance(result, pl.DataFrame)
        assert result["doubled"][0] == 84
