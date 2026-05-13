import polars as pl
import pytest


def _make_spec():
    from mountainash_pipelines.core.spec import PipelineSpec
    from mountainash_pipelines.core.step import StepDefinition
    return PipelineSpec(
        name="test",
        version="1.0.0",
        steps={"fetch": StepDefinition(name="fetch", fn=lambda ctx: [{"id": 1}])},
    )


class MockExecutor:
    def execute(self, pipeline, step_name, predicates, data_key=None):
        return pl.DataFrame([{"id": 1, "value": 42}]).lazy()


def test_visit_pipeline_step_rel_with_executor():
    from mountainash_pipelines.integration.relation import PipelineStepRelNode
    from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor
    from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem

    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=_make_spec(),
        executor=MockExecutor(),
    )

    visitor = UnifiedRelationVisitor(
        relation_system=PolarsRelationSystem(),
        expression_visitor=None,
    )

    result = visitor.visit_pipeline_step_rel(node)
    assert isinstance(result, pl.LazyFrame)
    collected = result.collect()
    assert collected.shape == (1, 2)
    assert collected["id"][0] == 1


def test_visit_pipeline_step_rel_no_executor_raises():
    from mountainash_pipelines.integration.relation import PipelineStepRelNode
    from mountainash.relations.core.unified_visitor.relation_visitor import UnifiedRelationVisitor
    from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem

    node = PipelineStepRelNode(step_name="fetch", pipeline=_make_spec())

    visitor = UnifiedRelationVisitor(
        relation_system=PolarsRelationSystem(),
        expression_visitor=None,
    )

    with pytest.raises(ValueError, match="[Nn]o executor"):
        visitor.visit_pipeline_step_rel(node)
