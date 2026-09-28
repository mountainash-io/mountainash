"""Set inputs execute at the resolved first input's physical location."""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.core.transit import BoundaryKey
from mountainash.relations.core.errors import UnsupportedRelationTransportError

IBIS_BACKENDS = [name for name, spec in REGISTRY.items() if spec.family == "ibis"]


@pytest.mark.parametrize("source_name", IBIS_BACKENDS)
@pytest.mark.parametrize("target_name", IBIS_BACKENDS)
@pytest.mark.parametrize("distinct,expected", [(False, [2, 2, 3]), (True, [2, 3])])
def test_union_uses_targeted_first_join_connection(source_name, target_name, distinct, expected):
    a = REGISTRY[source_name].build({"id": [2, 3]}, "a")
    b = REGISTRY[target_name].build({"id": [2]}, "b")
    first = ma.relation(a).join(b, on="id", execute_on="right").select("id")
    out = ma.concat([first, ma.relation(a).filter(ma.col("id") > 1)], distinct=distinct).collect()
    assert out._find_backend(use_default=False) is b._find_backend(use_default=False)
    assert sorted(ma.relation(out).to_dict()["id"]) == expected


@pytest.mark.parametrize("distinct", [False, True])
def test_prepared_union_preserves_native_child_typeerror(monkeypatch, distinct):
    """A child read failure is never interpreted as permission to coerce its data."""
    left = REGISTRY["polars"].build({"id": [1]}, "left")
    right = REGISTRY["polars"].build({"id": [2]}, "right")
    from mountainash.relations.backends.relation_systems.polars import PolarsRelationSystem

    original = PolarsRelationSystem.read

    def read(self, dataframe):
        if dataframe is right:
            raise TypeError("native right read failed")
        return original(self, dataframe)

    monkeypatch.setattr(PolarsRelationSystem, "read", read)
    with pytest.raises(TypeError, match="native right read failed"):
        ma.concat([ma.relation(left), ma.relation(right)], distinct=distinct).collect()


@pytest.mark.parametrize("distinct,expected", [(False, [1, 2, 2]), (True, [1, 2])])
@pytest.mark.parametrize("derived", [False, True])
def test_union_polars_first_transports_pandas_direct_and_derived(distinct, expected, derived):
    left = ma.relation(pl.DataFrame({"id": [1]}))
    right = ma.relation(pd.DataFrame({"id": [2, 2]}))
    if derived:
        right = right.filter(ma.col("id") > 0)
    assert sorted(ma.concat([left, right], distinct=distinct).to_dict()["id"]) == expected


@pytest.mark.parametrize("distinct,expected", [(False, [2, 2, 3]), (True, [2, 3])])
def test_targeted_first_union_exports_foreign_input_only(monkeypatch, distinct, expected):
    """One foreign derived input moves to the first join's selected connection."""
    import mountainash.relations.core.execution.transport as transport

    a = REGISTRY["ibis-duckdb"].build({"id": [2, 3]}, "a")
    b = REGISTRY["ibis-sqlite"].build({"id": [2]}, "b")
    first = ma.relation(a).join(b, on="id", execute_on="right").select("id")
    second = ma.relation(a).filter(ma.col("id") > 1)
    third = ma.relation(b).filter(ma.col("id") < 0)
    boundaries = []
    real = transport.transit_call

    def observed(boundary, fn, *args, **kwargs):
        boundaries.append(boundary)
        return real(boundary, fn, *args, **kwargs)

    monkeypatch.setattr(transport, "transit_call", observed)
    out = ma.concat([first, second, third], distinct=distinct).collect()
    assert out._find_backend(use_default=False) is b._find_backend(use_default=False)
    assert sorted(ma.relation(out).to_dict()["id"]) == expected
    assert boundaries.count(BoundaryKey.IBIS_TO_ARROW_EGRESS) == 2  # join left and union input
    assert boundaries.count(BoundaryKey.ARROW_TO_IBIS_ADAPTER) == 2


@pytest.mark.parametrize("named", [False, True])
@pytest.mark.parametrize("derived", [False, True])
@pytest.mark.parametrize("distinct,expected", [
    (False, [2, 2, 2, 3, 3, 3]), (True, [2, 3]),
])
def test_targeted_first_set_moves_only_foreign_sources(
    monkeypatch, named, derived, distinct, expected,
):
    """The join and a separate A operand each cross to B, but B never does."""
    from mountainash.relations.core.execution.transport import TransportSession

    a = REGISTRY["ibis-duckdb"].build({"id": [2, 3]}, "source")
    other_a = REGISTRY["ibis-duckdb"].build({"id": [2, 3]}, "other_source")
    b = REGISTRY["ibis-sqlite"].build({"id": [2, 3]}, "target")
    dag = ma.RelationDAG()
    dag.add("source", ma.relation(a))
    dag.add("other_source", ma.relation(other_a))
    dag.add("target", ma.relation(b))
    left = dag.ref("source") if named else ma.relation(a)
    right = dag.ref("target") if named else ma.relation(b)
    other = (dag.ref("other_source") if named else ma.relation(other_a))
    if derived:
        other = other.filter(ma.col("id") > 2)
        expected = [2, 2, 3, 3, 3] if not distinct else [2, 3]
    first = left.join(right, on="id", execute_on="right").select("id")
    relation = ma.concat([first, other, right], distinct=distinct)
    if named:
        dag.add("result", relation)
    moves = []
    real = TransportSession._convert

    def observed(self, source, requirement):
        moves.append((source.location.connection, requirement.destination.connection))
        return real(self, source, requirement)

    monkeypatch.setattr(TransportSession, "_convert", observed)
    result = dag.collect("result") if named else relation.collect()
    assert result._find_backend(use_default=False) is b._find_backend(use_default=False)
    assert sorted(ma.relation(result).to_dict()["id"]) == expected
    assert moves == [
        (a._find_backend(use_default=False), b._find_backend(use_default=False)),
        (other_a._find_backend(use_default=False), b._find_backend(use_default=False)),
    ]


@pytest.mark.parametrize("named", [False, True])
@pytest.mark.parametrize("distinct", [False, True])
def test_targeted_first_set_rejects_missing_route_before_native_union(
    monkeypatch, named, distinct,
):
    """A lazy Narwhals destination has no declared foreign-input adapter."""
    from mountainash.relations.backends.relation_systems.narwhals.substrait.relsys_nw_set import SubstraitNarwhalsSetRelationSystem

    b = REGISTRY["narwhals-lazy"].build({"id": [1, 2]}, "target")
    a = REGISTRY["ibis-duckdb"].build({"id": [2]}, "foreign")
    dag = ma.RelationDAG()
    dag.add("target", ma.relation(b))
    dag.add("foreign", ma.relation(a))
    target = dag.ref("target") if named else ma.relation(b)
    foreign = dag.ref("foreign") if named else ma.relation(a)
    first = target.join(target, on="id", execute_on="right").select("id")
    relation = ma.concat([first, foreign], distinct=distinct)
    if named:
        dag.add("result", relation)

    def forbidden(*args, **kwargs):
        raise AssertionError("native union ran before missing-route preflight")

    monkeypatch.setattr(type(a), "to_pyarrow", forbidden)
    monkeypatch.setattr(SubstraitNarwhalsSetRelationSystem, "union_all", forbidden)
    monkeypatch.setattr(SubstraitNarwhalsSetRelationSystem, "union_distinct", forbidden)
    with pytest.raises(UnsupportedRelationTransportError) as caught:
        if named:
            dag.collect("result")
        else:
            relation.collect()
    assert caught.value.destination_family == "narwhals"
    assert caught.value.source_family == "ibis"


def test_equivalent_unnamed_derived_set_operands_do_not_share_transfer(monkeypatch):
    from mountainash.relations.core.execution.transport import TransportSession

    a = REGISTRY["ibis-duckdb"].build({"id": [2, 3]}, "source")
    b = REGISTRY["ibis-sqlite"].build({"id": [2, 3]}, "target")
    first = ma.relation(a).join(b, on="id", execute_on="right").select("id")
    # Separate occurrences of the same recipe are not the same materialized operand.
    second = ma.relation(a).filter(ma.col("id") > 2)
    third = ma.relation(a).filter(ma.col("id") > 2)
    real = TransportSession._convert
    moves = []

    def observed(self, source, requirement):
        moves.append(source.source_token)
        return real(self, source, requirement)

    monkeypatch.setattr(TransportSession, "_convert", observed)
    result = ma.concat([first, second, third]).collect()
    assert result._find_backend(use_default=False) is b._find_backend(use_default=False)
    assert sorted(ma.relation(result).to_dict()["id"]) == [2, 3, 3, 3]
    assert len(moves) == len(set(moves)) == 3
