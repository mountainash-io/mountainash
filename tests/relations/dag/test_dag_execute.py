"""Cross-backend tests for RelationDAG.execute() — ad-hoc query execution."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


def _extract_column(result, col: str) -> list:
    """Extract a column from a backend-native result as a plain list."""
    if hasattr(result, "execute"):
        return result.execute()[col].tolist()
    if hasattr(result, "collect"):
        return result.collect()[col].to_list()
    return list(result[col])


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExecuteSimpleRef:
    def test_execute_simple_ref(self, backend_name, backend_factory):
        """Execute a relation referencing one DAG table."""
        data = {"id": [1, 2], "amount": [10, 20]}
        df = backend_factory.create(data, backend_name)
        dag = RelationDAG()
        dag.add("orders", ma.relation(df))
        rel = dag.ref("orders").filter(ma.col("amount").gt(15))
        result = dag.execute(rel)
        assert _extract_column(result, "id") == [2], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExecuteTransitiveRefs:
    def test_execute_transitive_refs(self, backend_name, backend_factory):
        """Execute a relation whose ref itself depends on another ref."""
        data = {"id": [1, 2, 3], "val": [5, 15, 25]}
        df = backend_factory.create(data, backend_name)
        dag = RelationDAG()
        dag.add("raw", ma.relation(df))
        dag.add("filtered", dag.ref("raw").filter(ma.col("val").gt(10)))
        rel = dag.ref("filtered").filter(ma.col("val").gt(20))
        result = dag.execute(rel)
        assert _extract_column(result, "id") == [3], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExecuteNoRefs:
    def test_execute_no_refs(self, backend_name, backend_factory):
        """Execute a relation with no RefRelNodes (inline data)."""
        data = {"a": [10], "b": [20]}
        df = backend_factory.create(data, backend_name)
        dag = RelationDAG()
        rel = ma.relation(df).filter(ma.col("a").gt(5))
        result = dag.execute(rel)
        assert _extract_column(result, "a") == [10], f"[{backend_name}]"


def test_execute_missing_ref():
    """Referencing a name not in the DAG raises KeyError."""
    dag = RelationDAG()
    rel = dag.ref("nonexistent").filter(ma.col("x").gt(0))
    with pytest.raises(KeyError, match="nonexistent"):
        dag.execute(rel)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExecuteDoesNotMutateDag:
    def test_execute_does_not_mutate_dag(self, backend_name, backend_factory):
        """execute() must not add relations or edges to the DAG."""
        data = {"x": [1]}
        df = backend_factory.create(data, backend_name)
        dag = RelationDAG()
        dag.add("src", ma.relation(df))
        relations_before = dict(dag.relations)
        edges_before = set(dag.dependency_edges)

        rel = dag.ref("src").filter(ma.col("x").gt(0))
        dag.execute(rel)

        assert dag.relations == relations_before
        assert dag.dependency_edges == edges_before


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExecuteMatchesCollect:
    def test_execute_matches_collect(self, backend_name, backend_factory):
        """execute() and collect() produce identical results."""
        data = {"id": [1, 2], "val": [10, 20]}
        df = backend_factory.create(data, backend_name)
        dag = RelationDAG()
        dag.add("data", ma.relation(df))

        rel = dag.ref("data").filter(ma.col("val").gt(15))
        result_execute = dag.execute(rel)

        dag.add("query", dag.ref("data").filter(ma.col("val").gt(15)))
        result_collect = dag.collect("query")

        assert (
            _extract_column(result_execute, "id")
            == _extract_column(result_collect, "id")
            == [2]
        ), f"[{backend_name}]"
