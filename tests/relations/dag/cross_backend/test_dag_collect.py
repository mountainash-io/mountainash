"""Cross-backend tests for RelationDAG.collect()."""
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


def _extract_sum(result, col: str):
    """Extract sum of a column from a backend-native result."""
    if hasattr(result, "execute"):
        return result.execute()[col].sum()
    if hasattr(result, "collect"):
        return result.collect()[col].sum()
    return sum(result[col])


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCollectSimple:
    def test_collect_simple(self, backend_name, backend_factory):
        data = {"id": [1, 2], "amount": [10, 20]}
        df = backend_factory.create(data, backend_name)
        dag = RelationDAG()
        dag.add("orders", ma.relation(df))
        result = dag.collect("orders")
        assert _extract_sum(result, "amount") == 30, f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCollectChain:
    def test_collect_chain(self, backend_name, backend_factory):
        data = {"id": [1, 2], "amount": [10, 20]}
        df = backend_factory.create(data, backend_name)
        dag = RelationDAG()
        dag.add("orders", ma.relation(df))
        dag.add("big", dag.ref("orders").filter(ma.col("amount").gt(15)))
        result = dag.collect("big")
        assert _extract_column(result, "id") == [2], f"[{backend_name}]"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCollectIndependentCalls:
    def test_collect_independent_calls(self, backend_name, backend_factory):
        data = {"x": [1]}
        df = backend_factory.create(data, backend_name)
        dag = RelationDAG()
        dag.add("a", ma.relation(df))
        dag.add("b", dag.ref("a"))
        dag.add("c", dag.ref("a"))
        rb = dag.collect("b")
        rc = dag.collect("c")
        assert (
            _extract_column(rb, "x")
            == _extract_column(rc, "x")
            == [1]
        ), f"[{backend_name}]"
