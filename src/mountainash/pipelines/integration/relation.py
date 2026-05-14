from __future__ import annotations

from typing import Any, ClassVar

from pydantic import ConfigDict

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.relations.core.unified_visitor.visit_registry import RelationVisitRegistry

from mountainash.pipelines.core.capabilities import PushedPredicates, StepCapabilities
from mountainash.pipelines.core.spec import PipelineSpec


class PipelineStepRelNode(RelationNode):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    _leaf_backend: ClassVar[CONST_BACKEND | None] = CONST_BACKEND.POLARS

    step_name: str
    pipeline: PipelineSpec
    data_key: str | None = None
    executor: Any | None = None
    capabilities: StepCapabilities = StepCapabilities()
    pushed_predicates: PushedPredicates = PushedPredicates()

    def accept(self, visitor: Any) -> Any:
        return visitor.visit(self)


def _visit_pipeline_step(node: Any, visitor: Any) -> Any:
    if node.executor is None:
        raise ValueError(
            f"No executor provided for PipelineStepRelNode '{node.step_name}'. "
            f"Pass an executor via source(..., executor=runner) or dag.add(..., executor=runner)."
        )
    return node.executor.execute(
        pipeline=node.pipeline,
        step_name=node.step_name,
        predicates=node.pushed_predicates,
        data_key=node.data_key,
    )


def register_pipeline_bridge() -> None:
    RelationVisitRegistry.register(PipelineStepRelNode, _visit_pipeline_step)
