from __future__ import annotations

from datetime import timedelta
from typing import Protocol

from mountainash_pipelines.core.result import StepResult


class PipelineStorage(Protocol):
    def write_step_output(self, step_name: str, result: StepResult) -> None: ...
    def read_step_output(self, step_name: str, cache_key: str) -> StepResult | None: ...
    def is_fresh(self, step_name: str, cache_key: str, max_age: timedelta | None = None) -> bool: ...
