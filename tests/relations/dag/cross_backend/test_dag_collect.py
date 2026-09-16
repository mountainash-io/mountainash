"""Cross-backend tests for RelationDAG.collect()."""

from __future__ import annotations

import pytest

import mountainash as ma
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
    return list(result[col])


def _extract_sum(result, col: str):
    """Extract sum of a column from a backend-native result."""
    # collect() before execute() — see _extract_column.
    if hasattr(result, "collect"):
        return result.collect()[col].sum()
    if hasattr(result, "execute"):
        return result.execute()[col].sum()
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
        assert _extract_column(rb, "x") == _extract_column(rc, "x") == [1], f"[{backend_name}]"


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_value_metadata_isolated_between_named_and_adhoc_resources(backend_name, backend_factory):
    numbers = backend_factory.create({"x": [0, 1]}, backend_name)
    text = backend_factory.create({"x": ["0", "1"]}, backend_name)
    dag = RelationDAG()
    dag.add("numbers", ma.relation(numbers))
    dag.add("text", ma.relation(text))
    expression = ma.col("x").value_kind().name.alias("kind")
    dag.add("numeric_kinds", dag.ref("numbers").select(expression))
    assert _extract_column(dag.collect("numeric_kinds"), "kind") == ["integer", "integer"]
    assert dag.ref("text").select(expression).to_dict() == {"kind": ["text", "text"]}
    assert _extract_column(dag.collect("numeric_kinds"), "kind") == ["integer", "integer"]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_transitive_metadata_gate_uses_each_prepared_ref(backend_name, backend_factory):
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.schema import CapabilityFact, CapabilityLevel, Clause, ClauseOp, Predicate
    from mountainash.core.constants import CONST_BACKEND
    from mountainash.core.types import BackendCapabilityError
    from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

    snapshot = CapabilityRegistry.snapshot()
    try:
        facts = {}
        for family in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS, CONST_BACKEND.IBIS):
            fact = CapabilityFact(
                operation_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS,
                param="x",
                level=CapabilityLevel.UNSUPPORTED,
                backend=family,
                message="transitive float operand blocked",
                since="2026-09-15",
                predicate=Predicate((Clause("__operand_types__.x.logical_kind", ClauseOp.EQ, "float"),)),
            )
            facts[family] = fact
            CapabilityRegistry.register_backend(family, [fact])
        dag = RelationDAG()
        expression = ma.col("x").abs().name.alias("result")
        dag.add("source", ma.relation(backend_factory.create({"x": [-2, 3]}, backend_name)))
        dag.add("integers", dag.ref("source").select(ma.col("x")))
        dag.add("floats", dag.ref("source").select(ma.col("x").cast(float).name.alias("x")))
        dag.add("integer_result", dag.ref("integers").select(expression))
        dag.add("float_result", dag.ref("floats").select(expression))
        assert _extract_column(dag.collect("integer_result"), "result") == [2, 3]
        with pytest.raises(BackendCapabilityError) as caught:
            dag.collect("float_result")
        limitation = caught.value.limitation
        assert limitation.fact_key == facts[limitation.backend].fact_key
        assert _extract_column(dag.collect("integer_result"), "result") == [2, 3]
    finally:
        CapabilityRegistry.restore(snapshot)
