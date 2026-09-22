import polars as pl
import pytest


def _make_spec():
    from mountainash.pipelines.core.spec import PipelineSpec
    from mountainash.pipelines.core.step import StepDefinition
    return PipelineSpec(
        name="test",
        version="1.0.0",
        steps={"fetch": StepDefinition(name="fetch", fn=lambda ctx: [{"id": 1}])},
    )


class MockExecutor:
    def execute(self, pipeline, step_name, params, data_key=None):
        return pl.DataFrame([{"id": 1, "value": 42}]).lazy()


def test_visit_pipeline_step_rel_with_executor():
    from mountainash.pipelines.integration.relation import PipelineStepRelNode
    from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor
    from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem
    from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
    from mountainash.core.constants import CONST_BACKEND

    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=_make_spec(),
        executor=MockExecutor(),
    )

    context = _new_execution_context(
        None, family_override=CONST_BACKEND.POLARS, policy=CapabilityPolicy.trusted(),
    )
    visitor = UnifiedRelationVisitor(
        relation_system=PolarsRelationSystem(),
        expression_visitor=None,
        execution_context=context,
    )

    result = visitor.visit(node)
    assert isinstance(result, pl.LazyFrame)
    collected = result.collect()
    assert collected.shape == (1, 2)
    assert collected["id"][0] == 1


def test_visit_pipeline_step_rel_no_executor_raises():
    from mountainash.pipelines.integration.relation import PipelineStepRelNode
    from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor
    from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem
    from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
    from mountainash.core.constants import CONST_BACKEND

    node = PipelineStepRelNode(step_name="fetch", pipeline=_make_spec())

    context = _new_execution_context(
        None, family_override=CONST_BACKEND.POLARS, policy=CapabilityPolicy.trusted(),
    )
    visitor = UnifiedRelationVisitor(
        relation_system=PolarsRelationSystem(),
        expression_visitor=None,
        execution_context=context,
    )

    with pytest.raises(ValueError, match="[Nn]o executor"):
        visitor.visit(node)
