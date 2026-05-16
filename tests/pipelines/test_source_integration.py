"""Integration tests: source() -> Relation -> collect() end-to-end."""
import polars as pl

import mountainash as ma
from mountainash.pipelines import source, pipeline
from mountainash.pipelines.core.step import step, StepContext
from mountainash.pipelines.core.capabilities import (
    StepCapabilities,
    PushableParam,
)
from mountainash.pipelines.storage.memory import MemoryPipelineStorage
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner


@step(name="fetch")
def fetch(ctx: StepContext) -> list[dict]:
    return [{"id": 1, "value": 42}]


received_predicates: list = []


@step(
    name="fetch_dated",
    pushdown=StepCapabilities(
        pushable_params=(
            PushableParam(column="start", api_param="start", operators=("gt", "gte"), format="iso_datetime"),
            PushableParam(column="start", api_param="end", operators=("lt", "lte"), format="iso_datetime_eod"),
        ),
    ),
)
def fetch_dated(ctx: StepContext) -> list[dict]:
    received_predicates.append(ctx.predicates)
    return [
        {"id": 1, "start": "2024-03-01", "value": 10},
        {"id": 2, "start": "2024-06-15", "value": 20},
    ]


def _make_runner(*steps):
    builder = pipeline("test", version="1.0.0")
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


class TestAutomaticPushdown:
    def test_filter_pushes_date_start(self):
        received_predicates.clear()
        runner, spec = _make_runner(fetch_dated)
        rel = source("fetch_dated", pipeline=spec, executor=runner.as_executor())
        result = rel.filter(ma.col("start").gt("2024-02-01")).collect()

        assert isinstance(result, pl.DataFrame)
        assert len(received_predicates) == 1
        assert "start" in received_predicates[0].params
        assert received_predicates[0].params["start"].value == "2024-02-01"
