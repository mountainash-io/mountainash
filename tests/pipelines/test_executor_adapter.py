"""Tests for _RunnerExecutorAdapter — LazyFrame conversion and data_key semantics."""
import polars as pl
import pytest

from mountainash.pipelines.core.step import step, StepContext
from mountainash.pipelines.core.capabilities import PushedPredicates
from mountainash.pipelines.fluent.builder import pipeline
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner
from mountainash.pipelines.storage.memory import MemoryPipelineStorage


@step(name="fetch_list")
def fetch_list(ctx: StepContext) -> list[dict]:
    return [{"id": 1, "value": 42}, {"id": 2, "value": 99}]


@step(name="fetch_empty")
def fetch_empty(ctx: StepContext) -> list[dict]:
    return []


@step(name="fetch_dict_multi")
def fetch_dict_multi(ctx: StepContext) -> dict:
    return {
        "activities": [{"id": 1, "type": "run"}],
        "metadata": {"count": 1},
    }


@step(name="fetch_dataframe")
def fetch_dataframe(ctx: StepContext) -> pl.DataFrame:
    return pl.DataFrame({"x": [10, 20]})


def _make_runner(*steps):
    builder = pipeline("test", version="1.0.0")
    for s in steps:
        builder = builder.step(s._step_definition.name, s)
    spec = builder.build()
    storage = MemoryPipelineStorage()
    return SimplePipelineRunner(spec=spec, storage=storage)


class TestExecutorAdapterReturnsLazyFrame:
    def test_list_of_dicts(self):
        runner = _make_runner(fetch_list)
        executor = runner.as_executor()
        result = executor.execute(
            pipeline=runner._spec,
            step_name="fetch_list",
            predicates=PushedPredicates(),
            data_key=None,
        )
        assert isinstance(result, pl.LazyFrame)
        df = result.collect()
        assert df.shape == (2, 2)
        assert df["value"].to_list() == [42, 99]

    def test_empty_list(self):
        runner = _make_runner(fetch_empty)
        executor = runner.as_executor()
        result = executor.execute(
            pipeline=runner._spec,
            step_name="fetch_empty",
            predicates=PushedPredicates(),
            data_key=None,
        )
        assert isinstance(result, pl.LazyFrame)
        df = result.collect()
        assert df.shape == (0, 0)

    def test_already_dataframe(self):
        runner = _make_runner(fetch_dataframe)
        executor = runner.as_executor()
        result = executor.execute(
            pipeline=runner._spec,
            step_name="fetch_dataframe",
            predicates=PushedPredicates(),
            data_key=None,
        )
        assert isinstance(result, pl.LazyFrame)
        df = result.collect()
        assert df["x"].to_list() == [10, 20]

    def test_data_key_extracts_subkey(self):
        runner = _make_runner(fetch_dict_multi)
        executor = runner.as_executor()
        result = executor.execute(
            pipeline=runner._spec,
            step_name="fetch_dict_multi",
            predicates=PushedPredicates(),
            data_key="activities",
        )
        assert isinstance(result, pl.LazyFrame)
        df = result.collect()
        assert df.shape == (1, 2)
        assert df["type"][0] == "run"

    def test_data_key_missing_raises(self):
        runner = _make_runner(fetch_dict_multi)
        executor = runner.as_executor()
        with pytest.raises(KeyError, match="data_key 'nope' not found"):
            executor.execute(
                pipeline=runner._spec,
                step_name="fetch_dict_multi",
                predicates=PushedPredicates(),
                data_key="nope",
            )

    def test_step_not_found_raises(self):
        runner = _make_runner(fetch_list)
        executor = runner.as_executor()
        with pytest.raises((KeyError, ValueError)):
            executor.execute(
                pipeline=runner._spec,
                step_name="missing",
                predicates=PushedPredicates(),
                data_key=None,
            )


class TestExecutorPassesTarget:
    def test_only_target_step_executes(self):
        """Runner should only execute the target step, not all steps."""
        call_log = []

        @step(name="expensive")
        def expensive(ctx: StepContext) -> list[dict]:
            call_log.append("expensive")
            return [{"x": 1}]

        @step(name="cheap")
        def cheap(ctx: StepContext) -> list[dict]:
            call_log.append("cheap")
            return [{"y": 2}]

        runner = _make_runner(expensive, cheap)
        executor = runner.as_executor()
        executor.execute(
            pipeline=runner._spec,
            step_name="cheap",
            predicates=PushedPredicates(),
            data_key=None,
        )
        assert "cheap" in call_log
        assert "expensive" not in call_log
