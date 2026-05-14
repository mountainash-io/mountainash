from __future__ import annotations

from typing import Any, Protocol

from mountainash.pipelines.core.capabilities import PushedPredicates
from mountainash.pipelines.core.spec import PipelineSpec


class PipelineExecutor(Protocol):
    def execute(
        self,
        pipeline: PipelineSpec,
        step_name: str,
        predicates: PushedPredicates,
        data_key: str | None,
    ) -> Any: ...
