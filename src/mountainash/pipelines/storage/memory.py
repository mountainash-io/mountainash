from __future__ import annotations

from datetime import datetime, timedelta

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.pipelines.core.result import StepResult


class MemoryPipelineStorage:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], StepResult] = {}

    def write_step_output(self, step_name: str, result: StepResult) -> None:
        self._store[(step_name, result.cache_key)] = result

    def read_step_output(self, step_name: str, cache_key: str) -> StepResult | None:
        return self._store.get((step_name, cache_key))

    def is_fresh(self, step_name: str, cache_key: str, max_age: timedelta | None = None) -> bool:
        result = self.read_step_output(step_name, cache_key)
        if result is None:
            return False
        if max_age is None:
            return True
        age = datetime.now() - result.metadata.completed_at
        return age <= max_age
