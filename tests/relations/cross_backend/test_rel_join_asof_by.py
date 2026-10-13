"""join_asof(by=...) must group-match, not be silently dropped (spec §3.6)."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


def test_join_asof_by_groups_polars():
    left = pl.DataFrame(
        {"g": ["a", "a", "b"], "t": [1, 5, 1], "v": [10, 20, 30]}
    ).sort("t")
    right = pl.DataFrame(
        {"g": ["a", "b"], "t": [0, 0], "r": [100, 200]}
    ).sort("t")
    out = (
        ma.relation(left)
        .join_asof(ma.relation(right), on="t", by="g")
        .to_polars()
        .sort(["g", "t"])
    )
    # With by-grouping, each row matches within its own group only.
    assert out["r"].to_list() == [100, 100, 200]


@pytest.mark.parametrize("by,expected_columns", [
    (None, ["g", "h", "t", "v", "g_right", "h_right", "v_right", "x"]),
    ("g", ["g", "h", "t", "v", "h_right", "v_right", "x"]),
    (["g", "h"], ["g", "h", "t", "v", "v_right", "x"]),
])
@pytest.mark.parametrize("strategy", ["backward", "forward", "nearest"])
def test_asof_schema_matches_execution(backend_name, backend_factory, by, expected_columns, strategy):
    from mountainash.core.types import BackendCapabilityError

    left, right = backend_factory.create_pair(
        {"g": ["a", "a"], "h": [1, 2], "t": [2, 4], "v": [10, 20]},
        {"g": ["a", "a"], "h": [1, 2], "t": [1, 3], "v": [100, 200], "x": ["x", "y"]},
        backend_name,
    )
    joined = ma.relation(left).join_asof(right, on="t", by=by, strategy=strategy)
    assert joined.columns == expected_columns
    if backend_name == "ibis-polars" and strategy != "backward":
        with pytest.raises(BackendCapabilityError):
            joined.to_polars()
        return
    actual = joined.to_polars().sort("t")
    assert actual.columns == expected_columns
    values = {
        "backward": [100, 200],
        "forward": [None, None] if isinstance(by, list) else [200, None],
        "nearest": [100, 200] if isinstance(by, list) else [200, 200],
    }
    assert actual["v_right"].to_list() == values[strategy]
    assert joined.select(*joined.columns).to_polars().sort("t").equals(actual)


def test_asof_empty_output_keeps_grouped_schema(backend_name, backend_factory):
    left, right = backend_factory.create_pair(
        {"g": ["a"], "t": [2], "v": [10]},
        {"g": ["a"], "t": [1], "v": [100]}, backend_name,
    )
    joined = ma.relation(left).head(0).join_asof(right, on="t", by="g")
    assert joined.columns == ["g", "t", "v", "v_right"]
    actual = joined.select(*joined.columns).to_polars()
    assert actual.to_dict(as_series=False) == {"g": [], "t": [], "v": [], "v_right": []}
