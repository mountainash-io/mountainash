from __future__ import annotations

from typing import Protocol, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.pipelines.core.result import StepResult
    from datetime import timedelta


class PipelineStorage(Protocol):
    def write_step_output(self, step_name: str, result: StepResult) -> None: ...
    def read_step_output(self, step_name: str, cache_key: str) -> StepResult | None: ...
    def is_fresh(self, step_name: str, cache_key: str, max_age: timedelta | None = None) -> bool: ...
