"""Public connectionless-Ibis placement and no-peer compatibility witnesses."""

import ibis
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.relations.core.errors import UnresolvedExecutionLocationError


IBIS = [name for name, spec in REGISTRY.items() if spec.family == "ibis"]


@pytest.mark.parametrize("backend_name", IBIS)
@pytest.mark.parametrize("selected_side", ["left", "right"])
def test_derived_memory_authority_binds_to_peer_in_both_positions(backend_name, selected_side, monkeypatch):
    source = REGISTRY["ibis-duckdb"].build({"id": [1, 2, 3], "value": [10, 20, 30]}, "source")
    memory = ibis.memtable(source.to_pyarrow())
    default = (ibis.duckdb.connect() if backend_name == "ibis-sqlite"
               else ibis.sqlite.connect(":memory:"))
    monkeypatch.setattr(ibis.options, "default_backend", default)
    peer = REGISTRY[backend_name].build({"id": [2], "peer": ["kept"]}, "peer")
    derived = ma.relation(memory).filter(ma.col("id") > 1)
    relation = (derived.join(peer, on="id", execute_on="left") if selected_side == "left"
                else ma.relation(peer).join(derived, on="id", execute_on="right"))
    try:
        native = relation.collect()
        assert native._find_backend(use_default=False) is peer._find_backend(use_default=False)
        assert ma.relation(native).to_dicts() == [{"id": 2, "value": 20, "peer": "kept"}]
    finally:
        default.disconnect()


@pytest.mark.parametrize("backend_name", IBIS)
def test_connectionless_first_set_chooses_first_bound_peer_with_native_values(backend_name):
    first_peer = REGISTRY[backend_name].build({"id": [1]}, "first_peer")
    other_peer = REGISTRY[backend_name].build({"id": [3]}, "other_peer")
    memory = ma.relation(ibis.memtable(pa.table({"id": [2]}))).filter(ma.col("id") > 0)
    result = ma.concat([memory, ma.relation(first_peer), ma.relation(other_peer)]).collect()
    assert result._find_backend(use_default=False) is first_peer._find_backend(use_default=False)
    assert sorted(ma.relation(result).to_dict()["id"]) == [1, 2, 3]


@pytest.mark.parametrize("configured_default", [False, True])
@pytest.mark.parametrize("terminal", ["collect", "to_polars"])
@pytest.mark.parametrize("operation", ["join", "union_all", "union_distinct"])
@pytest.mark.parametrize("peer_shape", ["polars", "pandas", "arrow", "mapping", "memtable"])
def test_standalone_memory_authority_rejects_no_peer_without_row_execution(
    monkeypatch, configured_default, terminal, operation, peer_shape,
):
    memory = ibis.memtable(pa.table({"id": [1]}))
    peer = {
        "polars": lambda: pl.DataFrame({"id": [1]}),
        "pandas": lambda: pd.DataFrame({"id": [1]}),
        "arrow": lambda: pa.table({"id": [1]}),
        "mapping": lambda: {"id": [1]},
        "memtable": lambda: ibis.memtable(pa.table({"id": [1]})),
    }[peer_shape]()
    default = ibis.duckdb.connect() if configured_default else None
    monkeypatch.setattr(ibis.options, "default_backend", default)
    original = type(memory)._find_backend

    def without_default(self, *, use_default=False):
        assert not use_default
        return original(self, use_default=False)

    def forbidden(*args, **kwargs):
        raise AssertionError("source rows were evaluated before no-peer rejection")

    monkeypatch.setattr(type(memory), "_find_backend", without_default)
    monkeypatch.setattr(type(memory), "to_pyarrow", forbidden)
    left, right = ma.relation(memory), ma.relation(peer)
    relation = left.join(right, on="id") if operation == "join" else ma.concat(
        [left, right], distinct=operation == "union_distinct",
    )
    try:
        with pytest.raises(UnresolvedExecutionLocationError):
            getattr(relation, terminal)()
    finally:
        if default is not None:
            default.disconnect()


def test_unbound_database_table_is_not_a_connectionless_memory_peer():
    bound = REGISTRY["ibis-duckdb"].build({"id": [1]}, "bound")
    unbound = ibis.table({"id": "int64"}, name="unbound")
    with pytest.raises(UnresolvedExecutionLocationError):
        ma.relation(unbound).join(bound, on="id").collect()
