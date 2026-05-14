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
