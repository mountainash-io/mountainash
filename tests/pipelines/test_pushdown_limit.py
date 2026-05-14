from mountainash.relations.core.relation_nodes.substrait.reln_fetch import FetchRelNode
from mountainash.pipelines.integration.relation import PipelineStepRelNode
from mountainash.pipelines.integration.pushdown import apply_pushdown
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import StepDefinition
from mountainash.pipelines.core.capabilities import (
    StepCapabilities,
    LimitCapability,
    PushedPredicates,
)


def _make_spec_with_limit_cap() -> PipelineSpec:
    return PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "fetch": StepDefinition(
                name="fetch",
                fn=lambda ctx: [],
                capabilities=StepCapabilities(
                    limit=LimitCapability(
                        max_limit=100,
                        supported_sort_columns=["date"],
                        supported_sort_directions=["asc", "desc"],
                    ),
                ),
            ),
        },
    )


def test_limit_pushdown_basic():
    spec = _make_spec_with_limit_cap()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    fetch_node = FetchRelNode(input=node, count=10)

    rewritten = apply_pushdown(fetch_node)

    assert isinstance(rewritten, FetchRelNode)
    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.limit == 10


def test_limit_capped_at_max():
    spec = _make_spec_with_limit_cap()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    fetch_node = FetchRelNode(input=node, count=500)

    rewritten = apply_pushdown(fetch_node)

    inner = rewritten.input
    assert inner.pushed_predicates.limit == 100  # capped at max_limit


def test_no_limit_pushdown_for_tail():
    spec = _make_spec_with_limit_cap()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    fetch_node = FetchRelNode(input=node, count=10, from_end=True)

    rewritten = apply_pushdown(fetch_node)

    inner = rewritten.input
    assert inner.pushed_predicates.limit is None


def test_no_limit_pushdown_without_capability():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={"fetch": StepDefinition(name="fetch", fn=lambda ctx: [])},
    )
    node = PipelineStepRelNode(step_name="fetch", pipeline=spec)
    fetch_node = FetchRelNode(input=node, count=10)

    rewritten = apply_pushdown(fetch_node)

    inner = rewritten.input
    assert inner.pushed_predicates.limit is None
