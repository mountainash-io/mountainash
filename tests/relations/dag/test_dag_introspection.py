"""Tests for RelationDAG introspection methods."""
import polars as pl
import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.relations.dag import RelationDAG


class TestDAGSchema:
    def test_schema_leaf_relation(self):
        dag = RelationDAG()
        dag.add("users", ma.relation(pl.LazyFrame({"id": [1], "name": ["a"]})))
        schema = dag.schema("users")
        assert list(schema.keys()) == ["id", "name"]
        # spec 2026-06-10-type-system-unification: schema values are canonical now
        assert schema["id"] == D.I64

    def test_schema_with_ref_dependency(self):
        dag = RelationDAG()
        dag.add("raw", ma.relation(pl.LazyFrame({"a": [1], "b": [2]})))
        filtered = dag.ref("raw").filter(ma.col("a").gt(0))
        dag.add("clean", filtered)
        schema = dag.schema("clean")
        assert list(schema.keys()) == ["a", "b"]

    def test_schema_conformed_relation(self):
        """dag.schema() reports correct columns for a conformed plan (item 44)."""
        from mountainash.typespec.spec import FieldDefinition, TableSchema
        from mountainash.typespec.universal_types import UniversalType

        dag = RelationDAG()
        dag.add("raw", ma.relation(pl.LazyFrame({"a": ["1"], "b": ["x"]})))
        spec = TableSchema(
            fields={"a": FieldDefinition(type=UniversalType.INTEGER)},
            fields_match="open",
        )
        dag.add("conformed", dag.ref("raw").conform(spec))
        schema = dag.schema("conformed")
        assert set(schema.keys()) == {"a", "b"}
        assert schema["a"] == D.I64

    def test_schema_unknown_name_raises(self):
        import pytest
        dag = RelationDAG()
        with pytest.raises(KeyError, match="not_here"):
            dag.schema("not_here")


class TestDAGDescribe:
    def test_describe_structure(self):
        dag = RelationDAG()
        dag.add("users", ma.relation(pl.LazyFrame({"id": [1], "name": ["a"]})))
        dag.add("orders", ma.relation(pl.LazyFrame({"oid": [1], "uid": [1]})))
        dag.constraint_edges.add(("users", "orders"))
        desc = dag.describe()
        assert "users" in desc
        assert "orders" in desc
        assert desc["users"]["columns"] == 2
        assert desc["orders"]["columns"] == 2
        assert desc["orders"]["constrained_by"] == ["users"]
        assert desc["users"]["dependencies"] == []

    def test_describe_with_dependencies(self):
        dag = RelationDAG()
        dag.add("raw", ma.relation(pl.LazyFrame({"a": [1]})))
        dag.add("derived", dag.ref("raw").select("a"))
        desc = dag.describe()
        assert desc["derived"]["dependencies"] == ["raw"]


class TestDAGToDot:
    def test_to_dot_basic_structure(self):
        dag = RelationDAG()
        dag.add("users", ma.relation(pl.LazyFrame({"id": [1]})))
        dag.add("orders", ma.relation(pl.LazyFrame({"oid": [1]})))
        dag.constraint_edges.add(("users", "orders"))
        dot = dag.to_dot()
        assert "digraph" in dot
        assert '"users"' in dot
        assert '"orders"' in dot
        assert "dashed" in dot

    def test_to_dot_dependency_edges(self):
        dag = RelationDAG()
        dag.add("raw", ma.relation(pl.LazyFrame({"a": [1]})))
        dag.add("derived", dag.ref("raw").select("a"))
        dot = dag.to_dot()
        assert '"raw" -> "derived"' in dot


class TestKernelOwnedStructure:
    """Structure (edges, ordering, DOT skeleton) comes from the graph kernel; introspection layers schema info on top."""

    def _dag(self):
        dag = RelationDAG()
        dag.add("raw", ma.relation(pl.LazyFrame({"a": [1], "b": [2]})))
        dag.add("derived", dag.ref("raw").select("a"))
        dag.add("other", ma.relation(pl.LazyFrame({"id": [1]})))
        dag.constraint_edges.add(("other", "derived"))
        return dag

    def test_to_dot_exact_output_pinned(self):
        assert self._dag().to_dot() == "\n".join([
            "digraph RelationDAG {",
            "    rankdir=BT;",
            '    "derived" [label="derived (1 cols)"];',
            '    "other" [label="other (1 cols)"];',
            '    "raw" [label="raw (2 cols)"];',
            '    "raw" -> "derived";',
            '    "other" -> "derived" [style=dashed, label="FK"];',
            "}",
        ])

    def test_describe_exact_output_pinned(self):
        assert self._dag().describe() == {
            "raw": {"columns": 2, "dependencies": [], "constrained_by": []},
            "derived": {"columns": 1, "dependencies": ["raw"], "constrained_by": ["other"]},
            "other": {"columns": 1, "dependencies": [], "constrained_by": []},
        }

    def test_structure_is_delegated_to_the_kernel(self, monkeypatch):
        from mountainash.graph.container import Graph

        calls = []
        real_describe, real_dot = Graph.describe, Graph.to_dot
        monkeypatch.setattr(Graph, "describe", lambda self: calls.append("describe") or real_describe(self))
        monkeypatch.setattr(Graph, "to_dot", lambda self, **kw: calls.append("to_dot") or real_dot(self, **kw))
        dag = self._dag()
        dag.describe()
        dag.to_dot()
        assert calls == ["describe", "to_dot"]


class TestTraversalReexport:
    """The relation-tree traversal helpers are part of the public package surface."""

    def test_helpers_importable_from_package(self):
        import mountainash.relations.dag as dag_pkg
        from mountainash.relations.dag import relation_children, walk_refs

        assert callable(relation_children)
        assert callable(walk_refs)
        assert "relation_children" in dag_pkg.__all__
        assert "walk_refs" in dag_pkg.__all__

    def test_walk_refs_collects_ref_names(self):
        from mountainash.relations.dag import walk_refs

        dag = RelationDAG()
        dag.add("raw", ma.relation(pl.LazyFrame({"a": [1]})))
        derived = dag.ref("raw").select("a")
        assert walk_refs(derived._node) == {"raw"}

    def test_relation_children_returns_structural_children(self):
        from mountainash.relations.dag import relation_children

        dag = RelationDAG()
        dag.add("raw", ma.relation(pl.LazyFrame({"a": [1]})))
        # ProjectRelNode over a single input relation.
        node = dag.ref("raw").select("a")._node
        assert len(relation_children(node)) == 1
