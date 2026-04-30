"""Cross-backend DAG integration for count_rows() and item() terminals."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations import relation
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.errors import RelationDAGRequired


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
    if hasattr(result, "collect") and not hasattr(result, "to_list"):
        return result.collect()[col].to_list()
    if hasattr(result, "to_list"):
        return result[col].to_list()
    return list(result[col])


def _extract_row_count(result) -> int:
    """Extract row count from a backend-native result."""
    if hasattr(result, "execute"):
        return len(result.execute())
    if hasattr(result, "collect") and not hasattr(result, "shape"):
        return len(result.collect())
    if hasattr(result, "shape"):
        return result.shape[0]
    return len(result)


# Error-path tests — backend-agnostic, no parametrization needed

def test_count_rows_standalone_on_ref_raises():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}, {"id": 2}]))
    ref_rel = dag.ref("orders")
    with pytest.raises(RelationDAGRequired):
        ref_rel.count_rows()


def test_item_standalone_on_ref_raises():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}]))
    ref_rel = dag.ref("orders")
    with pytest.raises(RelationDAGRequired):
        ref_rel.item("id")


# Cross-backend collect-then-check tests

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDagCollectThenCheck:
    def test_dag_collect_then_count_rows(self, backend_name, backend_factory):
        df = backend_factory.create({"id": [1, 2, 3]}, backend_name)
        dag = RelationDAG()
        dag.add("orders", ma.relation(df))
        dag.add(
            "filtered",
            dag.ref("orders").filter(ma.col("id").gt(ma.lit(1))),
        )
        native = dag.collect("filtered")
        assert _extract_row_count(native) == 2, f"[{backend_name}]"

    def test_dag_collect_then_item(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"id": [1, 2], "name": ["alice", "bob"]}, backend_name
        )
        dag = RelationDAG()
        dag.add("orders", ma.relation(df))
        dag.add("first", dag.ref("orders").head(1))
        native = dag.collect("first")
        values = _extract_column(native, "name")
        assert values[0] == "alice", f"[{backend_name}]"
