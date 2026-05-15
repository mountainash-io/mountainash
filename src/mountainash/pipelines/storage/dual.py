from __future__ import annotations


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.pipelines.storage.filesystem import FileSystemPipelineStorage
    from mountainash.pipelines.storage.memory import MemoryPipelineStorage
    from mountainash.pipelines.core.result import StepResult
    from datetime import timedelta


class DualPipelineStorage:
    def __init__(self, memory: MemoryPipelineStorage, filesystem: FileSystemPipelineStorage) -> None:
        self._memory = memory
        self._filesystem = filesystem

    def write_step_output(self, step_name: str, result: StepResult) -> None:
        self._memory.write_step_output(step_name, result)
        self._filesystem.write_step_output(step_name, result)

    def read_step_output(self, step_name: str, cache_key: str) -> StepResult | None:
        result = self._memory.read_step_output(step_name, cache_key)
        if result is not None:
            return result
        result = self._filesystem.read_step_output(step_name, cache_key)
        if result is not None:
            self._memory.write_step_output(step_name, result)
        return result

    def is_fresh(self, step_name: str, cache_key: str, max_age: timedelta | None = None) -> bool:
        if self._memory.is_fresh(step_name, cache_key, max_age):
            return True
        return self._filesystem.is_fresh(step_name, cache_key, max_age)
