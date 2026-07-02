from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    ResourceReadRelNode,
)
from mountainash.typespec.datapackage import DataResource


def test_resource_read_rel_node_holds_resource():
    res = DataResource(name="orders", path="orders.csv", format="csv")
    node = ResourceReadRelNode(resource=res)
    assert node.resource is res


def test_resource_read_rel_node_dispatches():
    """ResourceReadRelNode.accept() routes through visitor.visit() (registry dispatch)."""
    seen = []

    class V:
        def visit(self, node):
            seen.append(node.resource.name)
            return "visited"

    res = DataResource(name="orders", path="orders.csv")
    assert ResourceReadRelNode(resource=res).accept(V()) == "visited"
    assert seen == ["orders"]


def test_resource_read_rel_node_threads_resource_name_into_drift():
    """item 48 Task 7: _visit_resource_read_rel passes resource.name through
    to apply_conform(resource_name=...), which lands on the ConformDrift."""
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor
    from mountainash.expressions.core.expression_system.expsys_base import (
        get_expression_system,
    )
    from mountainash.relations.core.relation_protocols.relsys_base import (
        get_relation_system,
    )
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType

    backend = CONST_BACKEND.POLARS
    rel_sys = get_relation_system(backend)()
    expr_sys = get_expression_system(backend)()
    expr_visitor = UnifiedExpressionVisitor(expr_sys)
    visitor = UnifiedRelationVisitor(rel_sys, expr_visitor)

    spec = TypeSpec(fields=[FieldSpec(name="n", type=UniversalType.INTEGER)])
    res = DataResource(name="orders", type="table", data=[{"n": "1"}, {"n": "2"}], schema=spec)
    node = ResourceReadRelNode(resource=res)

    visitor.visit(node)

    assert len(visitor.drift_reports) == 1
    assert visitor.drift_reports[0].resource_name == "orders"
