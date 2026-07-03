"""join_asof(by=...) must group-match, not be silently dropped (spec §3.6)."""
from __future__ import annotations

import polars as pl

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
