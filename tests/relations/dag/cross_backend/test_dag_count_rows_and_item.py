"""Cross-backend DAG integration for count_rows() and item() terminals."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations import relation
from mountainash.relations.dag.dag import RelationDAG

from fixtures.backend_registry import ALL_BACKENDS

# ALL_BACKENDS = [
#     "polars",
#     "pandas",
#     "narwhals-polars",
#     "narwhals-pandas",
#     "ibis-polars",
#     "ibis-duckdb",
#     "ibis-sqlite",
# ]


def _extract_column(result, col: str) -> list:
    """Extract a column from a backend-native result as a plain list."""
    # collect() before execute(): a Polars LazyFrame has BOTH; we want the
    # subscriptable collect() result, not LazyFrame.execute()'s streaming
    # SingleNodeQueryResult. Ibis Tables only have execute().
    if hasattr(result, "collect"):
        return result.collect()[col].to_list()
    if hasattr(result, "execute"):
        return result.execute()[col].tolist()
    if hasattr(result, "to_list"):
        return result[col].to_list()
    return list(result[col])


def _extract_row_count(result) -> int:
    """Extract row count from a backend-native result."""
    # collect() before execute() — see _extract_column.
    if hasattr(result, "collect"):
        return len(result.collect())
    if hasattr(result, "execute"):
        return len(result.execute())
    if hasattr(result, "shape"):
        return result.shape[0]
    return len(result)


# DAGRelation terminal tests — backend-agnostic, no parametrization needed
#
# dag.ref() previously returned a plain Relation: its RefRelNode leaf had no
# DAG to resolve against, so a standalone terminal legitimately raised
# RelationDAGRequired. dag.ref() now returns a DAGRelation (PR-2 §2.2), which
# carries its DAG binding and routes terminals through
# RelationDAG._execute_with_visitor — the ref resolves and the terminal
# returns a real value instead of raising. (RelationDAGRequired is still
# raised for a *plain* Relation wrapping a bare RefRelNode with no DAG
# binding at all — see test_visitor_ref_resolver.py::test_ref_without_resolver_raises
# and test_rel_visit_registry.py::TestCoreHandlers::test_visit_ref_without_resolver.)

def test_count_rows_standalone_on_ref_resolves():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}, {"id": 2}]))
    ref_rel = dag.ref("orders")
    assert ref_rel.count_rows() == 2


def test_item_standalone_on_ref_resolves():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}]))
    ref_rel = dag.ref("orders")
    assert ref_rel.item("id") == 1


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
