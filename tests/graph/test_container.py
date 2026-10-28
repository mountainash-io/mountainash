import pytest

from mountainash.graph.container import Graph
from mountainash.graph.errors import CycleError, DuplicateNodeError, UnknownNodeError


def test_add_and_order_with_target_subset():
    g: Graph[str] = Graph()
    g.add("a", "A")
    g.add("b", "B", depends_on=["a"])
    g.add("c", "C", depends_on=["b"])
    g.add("x", "X")
    order = g.topological_order()
    assert set(order) == {"a", "b", "c", "x"} and order.index("a") < order.index("b") < order.index("c")
    assert g.topological_order(target="b") == ["a", "b"]
    assert g.ancestors("c") == {"a", "b"}
    assert g.descendants("a") == {"b", "c"}
    assert g.descendants("x") == set()


def test_duplicate_unknown_cycle():
    g: Graph[int] = Graph()
    g.add("a", 1)
    with pytest.raises(DuplicateNodeError):
        g.add("a", 2)
    with pytest.raises(UnknownNodeError):
        g.topological_order(target="zzz")
    g.add("b", 2, depends_on=["a"])
    g.dependency_edges.add(("b", "a"))
    with pytest.raises(CycleError):
        g.topological_order()


def test_constraint_edges_never_drive_order():
    g: Graph[int] = Graph()
    g.add("child", 1)
    g.add("parent", 2)
    g.add_constraint("parent", "child", meta={"fk": "id"})
    g.add_constraint("parent", "child", meta={"fk": "id"})  # equality-deduplicated
    assert ("parent", "child") in g.constraint_edges
    assert g.constraint_metadata[("parent", "child")] == [{"fk": "id"}]
    assert ("parent", "child") not in g.dependency_edges
    g.add_constraint("child", "parent")  # topology-only; would be a cycle if it drove order
    assert set(g.topological_order()) == {"child", "parent"}
    assert ("child", "parent") not in g.constraint_metadata


def test_layers_describe_dot():
    g: Graph[int] = Graph()
    g.add("a", 1)
    g.add("b", 2)
    g.add("c", 3, depends_on=["a", "b"])
    layers = g.parallel_layers(g.topological_order())
    assert [sorted(layer) for layer in layers] == [["a", "b"], ["c"]]
    assert g.describe()["c"] == {"depends_on": ["a", "b"], "constraints": []}
    dot = g.to_dot()
    assert dot.startswith("digraph") and '"a" -> "c"' in dot


def test_to_dot_is_parametrised_not_duplicated():
    g: Graph[int] = Graph()
    g.add("b", 2)
    g.add("a", 1)
    g.add("c", 3, depends_on=["a"])
    g.add_constraint("b", "c")
    assert g.to_dot() == "\n".join(
        ["digraph G {", '    "a";', '    "b";', '    "c";', '    "a" -> "c";', '    "b" -> "c" [style=dashed];', "}"]
    )
    dot = g.to_dot(
        name="X",
        graph_attrs=("rankdir=BT",),
        label=lambda n: f"{n}!",
        constraint_attrs=("style=dashed", 'label="FK"'),
    )
    assert dot == "\n".join(
        [
            "digraph X {", "    rankdir=BT;", '    "a" [label="a!"];', '    "b" [label="b!"];', '    "c" [label="c!"];',
            '    "a" -> "c";', '    "b" -> "c" [style=dashed, label="FK"];', "}",
        ]
    )
