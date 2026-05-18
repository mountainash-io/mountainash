from __future__ import annotations

from typing import Any, ClassVar

from pydantic import ConfigDict, Field

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.relations.core.unified_visitor.visit_registry import RelationVisitRegistry

from mountainash.pipelines.core.capabilities import ParamSpec


class PipelineStepRelNode(RelationNode):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    _leaf_backend: ClassVar[CONST_BACKEND | None] = CONST_BACKEND.POLARS

    step_name: str
    pipeline: Any
    data_key: str | None = None
    executor: Any | None = None
    param_specs: tuple[ParamSpec, ...] = ()
    bound_params: dict[str, Any] = Field(default_factory=dict)

    def accept(self, visitor: Any) -> Any:
        return visitor.visit(self)


class ParamsRelNode(RelationNode):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    _leaf_backend: ClassVar[CONST_BACKEND | None] = CONST_BACKEND.POLARS

    input: Any
    params: dict[str, Any] = Field(default_factory=dict)

    def accept(self, visitor: Any) -> Any:
        return visitor.visit(self)


def fold_params(node: Any) -> Any:
    if not isinstance(node, ParamsRelNode):
        return node
    if not isinstance(node.input, PipelineStepRelNode):
        return node

    pipeline_node: PipelineStepRelNode = node.input
    specs = pipeline_node.param_specs
    user_params = node.params

    if specs:
        spec_names = {s.name for s in specs}
        for name in user_params:
            if name not in spec_names:
                raise ValueError(
                    f"Unknown parameter '{name}'. "
                    f"Accepted: {sorted(spec_names)}"
                )

    merged = dict(pipeline_node.bound_params)
    for s in specs:
        if s.name in user_params:
            merged[s.name] = user_params[s.name]
        elif s.name not in merged and s.default is not None:
            merged[s.name] = s.default

    if specs:
        for s in specs:
            if s.required and s.name not in merged:
                raise ValueError(
                    f"Required parameter '{s.name}' not provided. "
                    f"Use .params({s.name}=...) to set it."
                )

    if not specs:
        merged.update(user_params)

    return PipelineStepRelNode(
        step_name=pipeline_node.step_name,
        pipeline=pipeline_node.pipeline,
        data_key=pipeline_node.data_key,
        executor=pipeline_node.executor,
        param_specs=pipeline_node.param_specs,
        bound_params=merged,
    )


def _visit_params(node: Any, visitor: Any) -> Any:
    """Visit a ParamsRelNode by folding params and visiting the result.

    If optimisation did not fold the ParamsRelNode (e.g. no optimisation pass ran),
    fold it now and visit the resulting node.
    """
    folded = fold_params(node)
    return visitor.visit(folded)


def _visit_pipeline_step(node: Any, visitor: Any) -> Any:
    if node.executor is None:
        raise ValueError(
            f"No executor provided for PipelineStepRelNode '{node.step_name}'. "
            f"Pass an executor via source(..., executor=runner) or dag.add(..., executor=runner)."
        )
    return node.executor.execute(
        pipeline=node.pipeline,
        step_name=node.step_name,
        params=node.bound_params,
        data_key=node.data_key,
    )


def register_pipeline_bridge() -> None:
    RelationVisitRegistry.register(PipelineStepRelNode, _visit_pipeline_step)
    RelationVisitRegistry.register(ParamsRelNode, _visit_params)


def register_params_optimisation() -> None:
    from mountainash.relations.core.relation_api.optimisation_registry import register_optimisation
    register_optimisation(ParamsRelNode, fold_params)
