import mountainash as ma
from mountainash.relations.core.relation_nodes.substrait.reln_project import ProjectRelNode
from mountainash.core.constants import ProjectOperation
from mountainash.expressions.core.expression_nodes.substrait.exn_field_reference import FieldReferenceNode
from mountainash.pipelines.integration.relation import PipelineStepRelNode
from mountainash.pipelines.integration.pushdown import apply_pushdown
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import StepDefinition
from mountainash.pipelines.core.capabilities import (
    StepCapabilities,
    FieldSelectionCapability,
    PushedPredicates,
)


def _make_spec_with_field_cap() -> PipelineSpec:
    return PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "fetch": StepDefinition(
                name="fetch",
                fn=lambda ctx: [],
                capabilities=StepCapabilities(
                    field_selection=FieldSelectionCapability(
                        available_fields=["id", "date", "value", "name"],
                        always_included=["id"],
                    ),
                ),
            ),
        },
    )


def test_field_selection_pushdown():
    spec = _make_spec_with_field_cap()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    # Construct SELECT project for ["date", "value"]
    project_node = ProjectRelNode(
        input=node,
        expressions=[FieldReferenceNode(field="date"), FieldReferenceNode(field="value")],
        operation=ProjectOperation.SELECT,
    )

    rewritten = apply_pushdown(project_node)

    # Project retained as residual
    assert isinstance(rewritten, ProjectRelNode)
    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    # "id" added from always_included
    assert sorted(inner.pushed_predicates.selected_fields) == ["date", "id", "value"]


def test_no_field_pushdown_without_capability():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={"fetch": StepDefinition(name="fetch", fn=lambda ctx: [])},
    )
    node = PipelineStepRelNode(step_name="fetch", pipeline=spec)
    project_node = ProjectRelNode(
        input=node,
        expressions=[FieldReferenceNode(field="date")],
        operation=ProjectOperation.SELECT,
    )

    rewritten = apply_pushdown(project_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.selected_fields is None


def test_field_pushdown_only_select_operation():
    """DROP and RENAME operations should NOT trigger field pushdown."""
    spec = _make_spec_with_field_cap()
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=spec,
        capabilities=spec.steps["fetch"].capabilities,
    )
    project_node = ProjectRelNode(
        input=node,
        expressions=[FieldReferenceNode(field="name")],
        operation=ProjectOperation.DROP,
    )

    rewritten = apply_pushdown(project_node)

    inner = rewritten.input
    assert isinstance(inner, PipelineStepRelNode)
    assert inner.pushed_predicates.selected_fields is None
