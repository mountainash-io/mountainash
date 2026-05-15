from __future__ import annotations

import pytest

from mountainash.graph.algorithms import ancestors, parallel_layers, topological_order


class TestTopologicalOrder:
    def test_linear_chain(self):
        nodes = {"a", "b", "c"}
        edges = {("a", "b"), ("b", "c")}
        result = topological_order(nodes, edges)
        assert result == ["a", "b", "c"]

    def test_diamond(self):
        nodes = {"a", "b", "c", "d"}
        edges = {("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")}
        result = topological_order(nodes, edges)
        assert result.index("a") < result.index("b")
        assert result.index("a") < result.index("c")
        assert result.index("b") < result.index("d")
        assert result.index("c") < result.index("d")

    def test_fan_out(self):
        nodes = {"root", "x", "y", "z"}
        edges = {("root", "x"), ("root", "y"), ("root", "z")}
        result = topological_order(nodes, edges)
        assert result[0] == "root"
        assert set(result[1:]) == {"x", "y", "z"}

    def test_fan_in(self):
        nodes = {"a", "b", "c", "sink"}
        edges = {("a", "sink"), ("b", "sink"), ("c", "sink")}
        result = topological_order(nodes, edges)
        assert result[-1] == "sink"
        assert set(result[:-1]) == {"a", "b", "c"}

    def test_single_node(self):
        assert topological_order({"a"}, set()) == ["a"]

    def test_empty_graph(self):
        assert topological_order(set(), set()) == []

    def test_cycle_raises(self):
        nodes = {"a", "b", "c"}
        edges = {("a", "b"), ("b", "c"), ("c", "a")}
        with pytest.raises(ValueError, match="Cycle detected"):
            topological_order(nodes, edges)

    def test_target_filtering(self):
        nodes = {"a", "b", "c", "d", "e"}
        edges = {("a", "b"), ("b", "c"), ("d", "e")}
        result = topological_order(nodes, edges, target="c")
        assert set(result) == {"a", "b", "c"}

    def test_target_not_in_nodes_raises(self):
        with pytest.raises(ValueError, match="not found"):
            topological_order({"a"}, set(), target="z")

    def test_deterministic_ordering(self):
        nodes = {"c", "b", "a"}
        edges: set[tuple[str, str]] = set()
        result1 = topological_order(nodes, edges)
        result2 = topological_order(nodes, edges)
        assert result1 == result2 == ["a", "b", "c"]


class TestAncestors:
    def test_direct_parent(self):
        edges = {("a", "b")}
        assert ancestors(edges, "b") == {"a"}

    def test_transitive(self):
        edges = {("a", "b"), ("b", "c")}
        assert ancestors(edges, "c") == {"a", "b"}

    def test_no_ancestors(self):
        edges = {("a", "b")}
        assert ancestors(edges, "a") == set()

    def test_diamond(self):
        edges = {("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")}
        assert ancestors(edges, "d") == {"a", "b", "c"}

    def test_empty_edges(self):
        assert ancestors(set(), "x") == set()


class TestParallelLayers:
    def test_linear_chain(self):
        edges = {("a", "b"), ("b", "c")}
        order = ["a", "b", "c"]
        assert parallel_layers(edges, order) == [["a"], ["b"], ["c"]]

    def test_diamond(self):
        edges = {("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")}
        order = topological_order({"a", "b", "c", "d"}, edges)
        layers = parallel_layers(edges, order)
        assert layers[0] == ["a"]
        assert set(layers[1]) == {"b", "c"}
        assert layers[2] == ["d"]

    def test_independent_nodes(self):
        edges: set[tuple[str, str]] = set()
        order = ["a", "b", "c"]
        layers = parallel_layers(edges, order)
        assert layers == [["a", "b", "c"]]

    def test_empty(self):
        assert parallel_layers(set(), []) == []
