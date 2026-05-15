from __future__ import annotations

from typing import Any, TYPE_CHECKING

from mountainash.relations.core.relation_api.relation import Relation

from mountainash.pipelines.integration.relation import PipelineStepRelNode

if TYPE_CHECKING:
    from mountainash.pipelines.core.spec import PipelineSpec


def source(
    step_name: str,
    *,
    pipeline: PipelineSpec,
    data_key: str | None = None,
    executor: Any | None = None,
) -> Relation:
    if step_name not in pipeline.steps:
        raise ValueError(f"Step '{step_name}' not found in pipeline '{pipeline.name}'")

    caps = pipeline.steps[step_name].capabilities
    node = PipelineStepRelNode(
        step_name=step_name,
        pipeline=pipeline,
        data_key=data_key,
        executor=executor,
        capabilities=caps,
    )

    return Relation(node)
