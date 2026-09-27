"""Set inputs execute at the resolved first input's physical location."""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.core.transit import BoundaryKey

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
