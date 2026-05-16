from mountainash.relations.core.relation_api.optimisation_registry import (
    register_optimisation,
    get_registered_node_types,
    get_passes,
    _reset_registry,
)


def test_register_and_retrieve():
    _reset_registry()

    class FakeNode:
        pass

    def fake_transform(node):
        return node

    register_optimisation(FakeNode, fake_transform)

    assert FakeNode in get_registered_node_types()
    passes = get_passes()
    assert len(passes) == 1
    assert passes[0] == (FakeNode, fake_transform)


def test_empty_registry():
    _reset_registry()
    assert get_registered_node_types() == set()
    assert get_passes() == []


def test_multiple_registrations():
    _reset_registry()

    class NodeA:
        pass

    class NodeB:
        pass

    register_optimisation(NodeA, lambda n: n)
    register_optimisation(NodeB, lambda n: n)

    assert get_registered_node_types() == {NodeA, NodeB}
    assert len(get_passes()) == 2
