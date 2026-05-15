from mountainash.pipelines.integration.relation import PipelineStepRelNode
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import StepDefinition
from mountainash.pipelines.core.capabilities import StepCapabilities, PushedPredicates


def _make_spec() -> PipelineSpec:
    return PipelineSpec(
        name="test",
        version="1.0.0",
        steps={"fetch": StepDefinition(name="fetch", fn=lambda ctx: [])},
    )


def test_pipeline_step_rel_node_creation():
    node = PipelineStepRelNode(
        step_name="fetch",
        pipeline=_make_spec(),
        data_key="sleep",
    )
    assert node.step_name == "fetch"
    assert node.data_key == "sleep"
    assert node.pushed_predicates == PushedPredicates()


class MockVisitor:
    def __init__(self):
        self.visited = None

    def visit(self, node):
        self.visited = node
        return "visited"


def test_pipeline_step_rel_node_accept():
    node = PipelineStepRelNode(step_name="fetch", pipeline=_make_spec())
    visitor = MockVisitor()
    result = node.accept(visitor)
    assert result == "visited"
    assert visitor.visited is node


def test_pipeline_step_rel_node_is_relation_node():
    from mountainash.relations.core.relation_nodes.reln_base import RelationNode
    node = PipelineStepRelNode(step_name="fetch", pipeline=_make_spec())
    assert isinstance(node, RelationNode)
