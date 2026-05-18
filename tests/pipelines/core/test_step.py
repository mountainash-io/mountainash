from __future__ import annotations

from datetime import date

from mountainash.pipelines.core.capabilities import ParamSpec
from mountainash.pipelines.core.step import StepDefinition, StepContext, step


class TestStepDefinition:
    def test_params_field(self):
        specs = (ParamSpec(name="start", type=date), ParamSpec(name="end", type=date))
        defn = StepDefinition(name="fetch", fn=lambda ctx: None, params=specs)
        assert defn.params == specs

    def test_params_default_empty(self):
        defn = StepDefinition(name="fetch", fn=lambda ctx: None)
        assert defn.params == ()


class TestStepContext:
    def test_params_field(self):
        ctx = StepContext(
            params={"start": date(2026, 4, 1), "end": date(2026, 5, 1)},
            pipeline_storage=None,
            storage_facade=None,
            config={},
            step_name="fetch",
            workflow_id=None,
        )
        assert ctx.params["start"] == date(2026, 4, 1)
        assert ctx.params["end"] == date(2026, 5, 1)


class TestStepDecorator:
    def test_decorator_with_params(self):
        specs = (ParamSpec(name="start", type=date),)

        @step(name="fetch", params=specs)
        def fetch(ctx):
            return []

        assert fetch._step_definition.params == specs
