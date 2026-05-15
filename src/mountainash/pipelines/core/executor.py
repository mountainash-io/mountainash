from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING


if TYPE_CHECKING:
    from mountainash.pipelines.core.spec import PipelineSpec
    from mountainash.pipelines.core.capabilities import PushedPredicates


class PipelineExecutor(Protocol):
    def execute(
        self,
        pipeline: PipelineSpec,
        step_name: str,
        predicates: PushedPredicates,
        data_key: str | None,
    ) -> Any: ...
