"""Tests for RelationDAG introspection methods."""
import polars as pl
import mountainash as ma
from mountainash.relations.dag import RelationDAG


class TestDAGSchema:
    def test_schema_leaf_relation(self):
        dag = RelationDAG()
        dag.add("users", ma.relation(pl.LazyFrame({"id": [1], "name": ["a"]})))
        schema = dag.schema("users")
        assert list(schema.keys()) == ["id", "name"]
        assert schema["id"] == pl.Int64

    def test_schema_with_ref_dependency(self):
        dag = RelationDAG()
        dag.add("raw", ma.relation(pl.LazyFrame({"a": [1], "b": [2]})))
        filtered = dag.ref("raw").filter(ma.col("a").gt(0))
        dag.add("clean", filtered)
        schema = dag.schema("clean")
        assert list(schema.keys()) == ["a", "b"]

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
