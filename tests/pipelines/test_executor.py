from __future__ import annotations

import pytest

from mountainash.pipelines.core.step import StepContext
from mountainash.pipelines.fluent.builder import pipeline
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner
from mountainash.pipelines.storage.memory import MemoryPipelineStorage


def _identity_step(ctx: StepContext) -> list[dict]:
    return [{"value": 1}]


class TestRunnerExecutorAdapter:
    def test_as_executor_returns_step_data(self):
        spec = pipeline("test", "v1").step("fetch", _identity_step).build()
        runner = SimplePipelineRunner(spec, MemoryPipelineStorage())
        executor = runner.as_executor()

        result = executor.execute(
            pipeline=spec,
            step_name="fetch",
            predicates=None,
            data_key=None,
        )
        assert result == [{"value": 1}]

    def test_as_executor_with_data_key(self):
        spec = pipeline("test", "v1").step("fetch", _identity_step).build()
        runner = SimplePipelineRunner(spec, MemoryPipelineStorage())
        executor = runner.as_executor()

        result = executor.execute(
            pipeline=spec,
            step_name="fetch",
            predicates=None,
            data_key="fetch",
        )
        assert result == [{"value": 1}]

    def test_as_executor_missing_step_raises(self):
        spec = pipeline("test", "v1").step("fetch", _identity_step).build()
        runner = SimplePipelineRunner(spec, MemoryPipelineStorage())
        executor = runner.as_executor()

        with pytest.raises(KeyError, match="not found"):
            executor.execute(
                pipeline=spec,
                step_name="fetch",
                predicates=None,
                data_key="nonexistent",
            )
