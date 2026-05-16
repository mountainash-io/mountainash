from datetime import date
import mountainash as ma
from mountainash.relations.core.relation_nodes.substrait.reln_filter import FilterRelNode
from mountainash.pipelines.integration.relation import PipelineStepRelNode
from mountainash.pipelines.integration.pushdown import apply_pushdown
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import StepDefinition
from mountainash.pipelines.core.capabilities import (
    StepCapabilities,
    PushableParam,
    PushedPredicates,
)


def _make_spec_with_date_params() -> PipelineSpec:
    return PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "fetch": StepDefinition(
                name="fetch",
                fn=lambda ctx: [],
                capabilities=StepCapabilities(
                    pushable_params=(
                        PushableParam(column="date", api_param="start", operators=("gt", "gte"), format="iso_datetime"),
                        PushableParam(column="date", api_param="end", operators=("lt", "lte"), format="iso_datetime_eod"),
                    ),
                ),
            ),
        },
    )


def test_pushdown_gt_date():
    spec = _make_spec_with_date_params()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("date").gt(ma.lit("2026-01-01"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    assert isinstance(rewritten, FilterRelNode)
    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert "start" in inner.pushed_predicates.params
    assert inner.pushed_predicates.params["start"].value == "2026-01-01"
    assert inner.pushed_predicates.params["start"].operator == "gt"
    assert inner.pushed_predicates.params["start"].format == "iso_datetime"


def test_pushdown_lt_date():
    spec = _make_spec_with_date_params()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("date").lt(ma.lit("2026-04-01"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert "end" in inner.pushed_predicates.params
    assert inner.pushed_predicates.params["end"].value == "2026-04-01"
    assert inner.pushed_predicates.params["end"].operator == "lt"


def test_pushdown_between_dates():
    spec = _make_spec_with_date_params()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("date").is_between(ma.lit("2026-01-01"), ma.lit("2026-04-01"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.params["start"].value == "2026-01-01"
    assert inner.pushed_predicates.params["start"].operator == "gte"
    assert inner.pushed_predicates.params["end"].value == "2026-04-01"
    assert inner.pushed_predicates.params["end"].operator == "lte"


def test_pushdown_and_expression():
    """AND of two comparisons pushes both bounds."""
    spec = _make_spec_with_date_params()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("date").gt(ma.lit("2026-01-01")) & ma.col("date").lt(ma.lit("2026-04-01"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.params["start"].value == "2026-01-01"
    assert inner.pushed_predicates.params["end"].value == "2026-04-01"


def test_pushdown_or_does_not_extract():
    """OR expressions cannot safely push either arm."""
    spec = _make_spec_with_date_params()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("date").gt(ma.lit("2026-01-01")) | ma.col("date").lt(ma.lit("2026-04-01"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.params == {}


def test_pushdown_generic_param():
    """Non-date params push down when declared."""
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "fetch": StepDefinition(
                name="fetch",
                fn=lambda ctx: [],
                capabilities=StepCapabilities(
                    pushable_params=(
                        PushableParam(column="sport_id", api_param="sportId", operators=("eq",)),
                    ),
                ),
            ),
        },
    )
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("sport_id").eq(ma.lit(5))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.params["sportId"].value == 5
    assert inner.pushed_predicates.params["sportId"].operator == "eq"


def test_no_pushdown_without_capability():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={"fetch": StepDefinition(name="fetch", fn=lambda ctx: [])},
    )
    node = PipelineStepRelNode(step_name="fetch", pipeline=spec)
    filter_expr = ma.col("date").gt(ma.lit("2026-01-01"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.params == {}


def test_residual_filter_always_retained():
    spec = _make_spec_with_date_params()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("date").gt(ma.lit("2026-01-01"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    assert isinstance(rewritten, FilterRelNode)
    assert rewritten.predicate is filter_node.predicate


def test_pushdown_wrong_column_ignored():
    spec = _make_spec_with_date_params()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("name").gt(ma.lit("abc"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.params == {}
