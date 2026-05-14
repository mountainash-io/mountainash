from datetime import date
import mountainash as ma
from mountainash.relations.core.relation_nodes.substrait.reln_filter import FilterRelNode
from mountainash.pipelines.integration.relation import PipelineStepRelNode
from mountainash.pipelines.integration.pushdown import apply_pushdown
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import StepDefinition
from mountainash.pipelines.core.capabilities import (
    StepCapabilities,
    DateRangeCapability,
    PushedPredicates,
)


def _make_spec_with_date_cap() -> PipelineSpec:
    return PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "fetch": StepDefinition(
                name="fetch",
                fn=lambda ctx: [],
                capabilities=StepCapabilities(
                    date_range=DateRangeCapability(column="date"),
                ),
            ),
        },
    )


def test_pushdown_gt_date():
    spec = _make_spec_with_date_cap()
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
    assert inner.pushed_predicates.date_start == date(2026, 1, 1)


def test_pushdown_lt_date():
    spec = _make_spec_with_date_cap()
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
    assert inner.pushed_predicates.date_end == date(2026, 4, 1)


def test_pushdown_between_dates():
    spec = _make_spec_with_date_cap()
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
    assert inner.pushed_predicates.date_start == date(2026, 1, 1)
    assert inner.pushed_predicates.date_end == date(2026, 4, 1)


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
    assert inner.pushed_predicates == PushedPredicates()


def test_residual_filter_always_retained():
    spec = _make_spec_with_date_cap()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    filter_expr = ma.col("date").gt(ma.lit("2026-01-01"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    # Filter MUST be retained as residual (correctness invariant)
    assert isinstance(rewritten, FilterRelNode)
    assert rewritten.predicate is filter_node.predicate


def test_pushdown_wrong_column_ignored():
    spec = _make_spec_with_date_cap()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    # Filter on "name" column, not "date" — should NOT push
    filter_expr = ma.col("name").gt(ma.lit("abc"))
    filter_node = FilterRelNode(input=node, predicate=filter_expr._node)

    rewritten = apply_pushdown(filter_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.date_start is None
