from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode


def test_ref_rel_node_minimal():
    node = RefRelNode(name="orders")
    assert node.name == "orders"
    assert node.output_schema is None


def test_ref_rel_node_with_schema_dict():
    # output_schema is intentionally Any so it accepts a raw frictionless schema dict
    # OR a TypeSpec, mirroring DataResource.table_schema in the rest of the project.
    schema = {"fields": [{"name": "x", "type": "integer"}]}
    node = RefRelNode(name="orders", output_schema=schema)
    assert node.output_schema == schema


def test_ref_rel_node_dispatches_to_visit():
    """RefRelNode.accept() routes through visitor.visit() (registry dispatch)."""
    seen = []

    class V:
        def visit(self, node):
            seen.append(node.name)
            return "visited"

    assert RefRelNode(name="x").accept(V()) == "visited"
    assert seen == ["x"]
