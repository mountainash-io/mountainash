from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from mountainash.pipelines.core.capabilities import ParamSpec
from mountainash.pipelines.core.policies import EmptyPolicy, RetryConfig
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import StepDefinition

if TYPE_CHECKING:
    from datetime import timedelta


class PipelineBuilder:
    def __init__(self, name: str, version: str) -> None:
        self._name = name
        self._version = version
        self._steps: dict[str, StepDefinition] = {}

    def step(
        self,
        name: str,
        fn: Callable,
        *,
        depends_on: list[str] | None = None,
        params: tuple[ParamSpec, ...] | None = None,
        retry: RetryConfig | None = None,
        cache_ttl: timedelta | None = None,
        empty_policy: EmptyPolicy = EmptyPolicy.WARN,
    ) -> PipelineBuilder:
        if name in self._steps:
            raise ValueError(f"Step '{name}' already exists in pipeline '{self._name}'")

        actual_fn = fn
        actual_deps = depends_on
        actual_params = params

        if hasattr(fn, "_step_definition"):
            defn: StepDefinition = fn._step_definition
            actual_fn = defn.fn
            if actual_deps is None:
                actual_deps = defn.depends_on
            if actual_params is None:
                actual_params = defn.params

        if actual_params is None and hasattr(fn, "_param_specs"):
            actual_params = fn._param_specs

        new_builder = PipelineBuilder(self._name, self._version)
        new_builder._steps = dict(self._steps)
        new_builder._steps[name] = StepDefinition(
            name=name,
            fn=actual_fn,
            depends_on=actual_deps or [],
            params=actual_params or (),
            retry=retry,
            cache_ttl=cache_ttl,
            empty_policy=empty_policy,
        )
        return new_builder

    def build(self) -> PipelineSpec:
        return PipelineSpec(name=self._name, version=self._version, steps=self._steps)
