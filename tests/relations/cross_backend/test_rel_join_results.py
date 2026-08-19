"""Cross-backend result verification for join operations.

Phase 2 of the relation result verification suite. Tests inner, left, right,
outer, semi, anti, cross joins, suffix disambiguation, multi-key joins, and
join_asof across all 7 backends.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma

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


def sorted_dicts(dicts: list[dict], by: str | list[str]) -> list[dict]:
    """Sort list of dicts by key(s) for order-independent comparison."""
    if isinstance(by, str):
        by = [by]
    return sorted(dicts, key=lambda d: tuple(
        (0, d[k]) if d[k] is not None else (1,) for k in by
    ))


# ---------------------------------------------------------------------------
# Inner Join
# ---------------------------------------------------------------------------

from fixtures.capability_gating import xfail_divergence

_ASOF = ALL_BACKENDS
_ASOF_DIRECTIONAL = [
    pytest.param(b, marks=xfail_divergence("IB-REL-15", backend=b)) for b in ALL_BACKENDS
]
_ASOF_TEMPORAL_NEAREST = [
    pytest.param(
        b,
        marks=(xfail_divergence("IB-REL-15", backend=b), xfail_divergence("IB-REL-14", backend=b)),
    )
    for b in ALL_BACKENDS
]
_ASOF_TOLERANCE = [
    pytest.param(b, marks=xfail_divergence("NW-REL-03", backend=b)) for b in ALL_BACKENDS
]
_ASOF_TEMPORAL_TOLERANCE = [
    pytest.param(
        b,
        marks=(xfail_divergence("NW-REL-03", backend=b), xfail_divergence("IB-REL-14", backend=b)),
    )
    for b in ALL_BACKENDS
]
_ASOF_NULL = [
    pytest.param(b, marks=xfail_divergence("NW-REL-04", backend=b)) for b in ALL_BACKENDS
]
_ASOF_DUP_RIGHT_BACKWARD = [
    pytest.param(b, marks=xfail_divergence("IB-REL-16", backend=b)) for b in ALL_BACKENDS
]
_ASOF_NEAREST_DUP = [
    pytest.param(
        b,
        marks=(
            xfail_divergence("IB-REL-15", backend=b),
            xfail_divergence("NW-REL-05", backend=b),
        ),
    )
    for b in ALL_BACKENDS
]
_ASOF_BY_GROUPING = [
    pytest.param(b, marks=xfail_divergence("IB-REL-17", backend=b)) for b in ALL_BACKENDS
]

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinInner:
    def test_inner_matching_rows(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"id": [1, 2, 3], "val": ["a", "b", "c"]},
            {"id": [2, 3, 4], "score": [20, 30, 40]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on="id", how="inner"
        ).to_dicts()
        result_sorted = sorted_dicts(result, "id")
        assert result_sorted == [
            {"id": 2, "val": "b", "score": 20},
            {"id": 3, "val": "c", "score": 30},
        ]

    def test_inner_no_match(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"id": [1, 2], "val": ["a", "b"]},
            {"id": [3, 4], "score": [30, 40]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on="id", how="inner"
        ).to_dicts()
        assert result == []


# ---------------------------------------------------------------------------
# Left Join
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinLeft:
    def test_left_null_fill(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"id": [1, 2, 3], "val": ["a", "b", "c"]},
            {"id": [2, 3], "score": [20, 30]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on="id", how="left"
        ).to_dicts()
        result_sorted = sorted_dicts(result, "id")
        assert result_sorted == [
            {"id": 1, "val": "a", "score": None},
            {"id": 2, "val": "b", "score": 20},
            {"id": 3, "val": "c", "score": 30},
        ]


# ---------------------------------------------------------------------------
# Right Join
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinRight:
    def test_right_null_fill(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"id": [1, 2], "val": ["a", "b"]},
            {"id": [2, 3], "score": [20, 30]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on="id", how="right"
        ).to_dicts()
        result_sorted = sorted_dicts(result, "id")
        assert result_sorted == [
            {"id": 2, "val": "b", "score": 20},
            {"id": 3, "val": None, "score": 30},
        ]


# ---------------------------------------------------------------------------
# Outer Join
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinOuter:
    def test_outer_both_side_null_fill(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"id": [1, 2], "val": ["a", "b"]},
            {"id": [2, 3], "score": [20, 30]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on="id", how="outer"
        ).to_dicts()
        result_sorted = sorted_dicts(result, "id")
        assert result_sorted == [
            {"id": 1, "val": "a", "score": None},
            {"id": 2, "val": "b", "score": 20},
            {"id": 3, "val": None, "score": 30},
        ]


# ---------------------------------------------------------------------------
# Semi Join
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinSemi:
    def test_semi_returns_left_columns_only(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"id": [1, 2, 3], "val": ["a", "b", "c"]},
            {"id": [2, 3, 4], "score": [20, 30, 40]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on="id", how="semi"
        ).to_dicts()
        result_sorted = sorted_dicts(result, "id")
        assert result_sorted == [
            {"id": 2, "val": "b"},
            {"id": 3, "val": "c"},
        ]


# ---------------------------------------------------------------------------
# Anti Join
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinAnti:
    def test_anti_excludes_matching(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"id": [1, 2, 3], "val": ["a", "b", "c"]},
            {"id": [2, 3, 4], "score": [20, 30, 40]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on="id", how="anti"
        ).to_dicts()
        result_sorted = sorted_dicts(result, "id")
        assert result_sorted == [
            {"id": 1, "val": "a"},
        ]


# ---------------------------------------------------------------------------
# Cross Join
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinCross:
    def test_cross_cartesian_product(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"a": [1, 2]},
            {"b": ["x", "y"]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, how="cross"
        ).to_dicts()
        result_sorted = sorted_dicts(result, ["a", "b"])
        assert result_sorted == [
            {"a": 1, "b": "x"},
            {"a": 1, "b": "y"},
            {"a": 2, "b": "x"},
            {"a": 2, "b": "y"},
        ]


# ---------------------------------------------------------------------------
# Join with Suffix (column disambiguation)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinSuffix:
    def test_suffix_disambiguation(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"id": [1, 2], "val": [10, 20]},
            {"id": [1, 2], "val": [100, 200]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on="id", how="inner", suffix="_r"
        ).to_dicts()
        result_sorted = sorted_dicts(result, "id")
        assert result_sorted == [
            {"id": 1, "val": 10, "val_r": 100},
            {"id": 2, "val": 20, "val_r": 200},
        ]


# ---------------------------------------------------------------------------
# Multi-Key Join
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinMultiKey:
    def test_join_on_two_columns(self, backend_name, backend_factory):
        left, right = backend_factory.create_pair(
            {"a": [1, 1, 2], "b": ["x", "y", "x"], "lv": [10, 20, 30]},
            {"a": [1, 2], "b": ["x", "x"], "rv": [100, 200]},
            backend_name,
        )
        result = ma.relation(left).join(
            right, on=["a", "b"], how="inner"
        ).to_dicts()
        result_sorted = sorted_dicts(result, ["a", "b"])
        assert result_sorted == [
            {"a": 1, "b": "x", "lv": 10, "rv": 100},
            {"a": 2, "b": "x", "lv": 30, "rv": 200},
        ]


# ---------------------------------------------------------------------------
# Asof Join
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _ASOF)
class TestJoinAsof:
    def test_asof_backward_strategy(self, backend_name, backend_factory):
        """Test asof join with backward strategy.

        join_asof matches each left row with the nearest right row where
        right.on <= left.on (backward strategy).
        """
        left, right = backend_factory.create_pair(
            {"t": [1, 3, 5, 7], "val": ["a", "b", "c", "d"]},
            {"t": [2, 4, 6], "score": [20, 40, 60]},
            backend_name,
        )
        result = ma.relation(left).join_asof(
            right, on="t", strategy="backward"
        ).to_dicts()
        # t=1: no right row <= 1, so score=None
        # t=3: right t=2 <= 3, so score=20
        # t=5: right t=4 <= 5, so score=40
        # t=7: right t=6 <= 7, so score=60
        assert len(result) == 4
        assert result[0]["val"] == "a"
        assert result[0]["score"] is None
        assert result[1]["val"] == "b"
        assert result[1]["score"] == 20
        assert result[2]["val"] == "c"
        assert result[2]["score"] == 40
        assert result[3]["val"] == "d"
        assert result[3]["score"] == 60

    def test_asof_duplicate_left_rows(self, backend_name, backend_factory):
        """Duplicate LEFT rows (not duplicate right keys — see
        test_asof_duplicate_right_keys for that, which DOES diverge on
        ibis-duckdb). This case has no ambiguity in which right row matches
        each left row, only in output ORDER among the two left rows sharing a
        key — which Task 3's determinism fix pins deterministically and
        correctly everywhere."""
        left_data = {"t": [5, 5], "val": ["r1", "r2"]}
        right_data = {"t": [4, 6], "score": [40, 60]}
        oracle = pl.DataFrame(left_data).join_asof(
            pl.DataFrame(right_data), on="t", strategy="backward"
        ).to_dicts()
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="backward").to_dicts()
        assert result == oracle

    def test_asof_temporal_keys(self, backend_name, backend_factory):
        """Temporal on-column, backward strategy (no distance computation needed —
        works everywhere unlike nearest/tolerance, see the gated-cell tests below)."""
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1)
        left_data = {"t": [base, base + timedelta(minutes=3)], "val": ["a", "b"]}
        right_data = {"t": [base + timedelta(minutes=1), base + timedelta(minutes=4)],
                      "score": [10, 40]}
        oracle = pl.DataFrame(left_data).join_asof(
            pl.DataFrame(right_data), on="t", strategy="backward"
        ).to_dicts()
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="backward").to_dicts()
        assert result == oracle


@pytest.mark.cross_backend
class TestJoinAsofGatedCells:
    def _oracle(self, left_data, right_data, **kwargs):
        return pl.DataFrame(left_data).join_asof(pl.DataFrame(right_data), **kwargs).to_dicts()

    @pytest.mark.parametrize("backend_name", _ASOF_DUP_RIGHT_BACKWARD)
    def test_asof_duplicate_right_keys(self, backend_name, backend_factory):
        """Backward keeps the LAST equal-key right row (Polars-probed).
        ibis-duckdb's NATIVE asof_join picks the FIRST — declared as
        IB-REL-16 rather than fixed, since the emulation (used everywhere
        else) and ibis-polars native (delegating to real Polars) both
        already match Polars on this."""
        left_data = {"t": [5], "val": ["x"]}
        right_data = {"t": [4, 4, 6], "score": [41, 42, 60]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="backward")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="backward").to_dicts()
        assert result == oracle

    @pytest.mark.parametrize("backend_name", _ASOF_BY_GROUPING)
    def test_asof_by_grouping(self, backend_name, backend_factory):
        """`by` groups are INTERLEAVED in the input (spec §7.1(5)) but `t` is
        globally ascending — pandas merge_asof requires global sortedness of
        `on` even with `by` set. IB-REL-17 declares that Ibis's SQL-backend
        paths group output by `by` value rather than preserving this
        interleaved order; every backend's matched VALUES are correct."""
        left_data = {"g": ["a", "b", "a", "b"], "t": [1, 2, 3, 4],
                     "val": ["a1", "b2", "a3", "b4"]}
        right_data = {"g": ["a", "b", "a", "b"], "t": [1, 2, 3, 5],
                      "score": [10, 20, 30, 50]}
        oracle = self._oracle(left_data, right_data, on="t", by="g", strategy="backward")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(
            right, on="t", by="g", strategy="backward"
        ).to_dicts()
        assert result == oracle

    @pytest.mark.parametrize("backend_name", _ASOF_DIRECTIONAL)
    def test_asof_forward_strategy(self, backend_name, backend_factory):
        left_data = {"t": [1, 3, 5, 7], "val": ["a", "b", "c", "d"]}
        right_data = {"t": [2, 4, 6], "score": [20, 40, 60]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="forward")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="forward").to_dicts()
        assert result == oracle

    @pytest.mark.parametrize("backend_name", _ASOF_DIRECTIONAL)
    def test_asof_nearest_strategy(self, backend_name, backend_factory):
        left_data = {"t": [1, 3, 5, 7], "val": ["a", "b", "c", "d"]}
        right_data = {"t": [2, 4, 6], "score": [20, 40, 60]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="nearest")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="nearest").to_dicts()
        assert result == oracle

    @pytest.mark.parametrize("backend_name", _ASOF_DIRECTIONAL)
    def test_asof_nearest_forward_tie(self, backend_name, backend_factory):
        """A GENUINE cross-side equidistant tie (right holds 4 and 6, left is
        5 — two DIFFERENT-valued candidates at equal distance). This is the
        core `nearest` correctness fix (Task 4) and has no declared
        divergence anywhere — forward-wins here on every backend."""
        left_data = {"t": [5], "val": ["x"]}
        right_data = {"t": [4, 6], "score": [40, 60]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="nearest")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="nearest").to_dicts()
        assert result == oracle  # forward-wins -> score 60

    @pytest.mark.parametrize("backend_name", _ASOF_NEAREST_DUP)
    def test_asof_nearest_duplicate_right_keys(self, backend_name, backend_factory):
        """An EXACT-match tie (right holds a duplicate exactly at the left
        key) — a duplicate-tie-winner question, not a cross-side-tie
        question. Declared via NW-REL-05 on narwhals-pandas/pandas rather
        than fixed."""
        left_data = {"t": [5], "val": ["x"]}
        right_data = {"t": [5, 5, 7], "score": [51, 52, 70]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="nearest")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="nearest").to_dicts()
        assert result == oracle  # score 52, the LAST t=5 duplicate

    @pytest.mark.parametrize("backend_name", _ASOF_DIRECTIONAL)
    def test_asof_nearest_colliding_payload_names(self, backend_name, backend_factory):
        """Left and right share a non-key column name (`val`) — Polars-parity
        schema suffixes the right one `val_right`, matching plain `join_asof`
        on every backend. This is a genuine crash fix (narwhals nearest
        previously raised `DuplicateError`), not a tie-break question — no
        divergence needed once fixed."""
        left_data = {"t": [1, 5], "val": ["L1", "L5"]}
        right_data = {"t": [3, 4], "val": ["R3", "R4"]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="nearest")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="nearest").to_dicts()
        assert result == oracle

    @pytest.mark.parametrize("backend_name", _ASOF_TEMPORAL_NEAREST)
    def test_asof_temporal_nearest_strategy(self, backend_name, backend_factory):
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1)
        left_data = {"t": [base, base + timedelta(minutes=3)], "val": ["a", "b"]}
        right_data = {"t": [base + timedelta(minutes=1), base + timedelta(minutes=4)],
                      "score": [10, 40]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="nearest")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="nearest").to_dicts()
        assert result == oracle

    @pytest.mark.parametrize("backend_name", _ASOF_TEMPORAL_TOLERANCE)
    def test_asof_temporal_tolerance(self, backend_name, backend_factory):
        """Natural/Polars-idiomatic calling convention: `tolerance` is a
        `datetime.timedelta` for a temporal `on` column. `strategy="backward"`
        here, so ibis-polars is NOT gated (only forward/nearest are) — the
        native path computes this with full Polars parity."""
        from datetime import datetime, timedelta
        base = datetime(2026, 1, 1)
        left_data = {"t": [base, base + timedelta(minutes=3)], "val": ["a", "b"]}
        right_data = {"t": [base + timedelta(minutes=1), base + timedelta(minutes=4)],
                      "score": [10, 40]}
        tol = timedelta(minutes=2)
        oracle = self._oracle(left_data, right_data, on="t", strategy="backward", tolerance=tol)
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(
            right, on="t", strategy="backward", tolerance=tol
        ).to_dicts()
        assert result == oracle

    @pytest.mark.parametrize("backend_name", _ASOF_TOLERANCE)
    def test_asof_tolerance(self, backend_name, backend_factory):
        left_data = {"t": [10, 20, 30], "val": ["a", "b", "c"]}
        right_data = {"t": [5, 27], "score": [50, 270]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="backward", tolerance=2)
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(
            right, on="t", strategy="backward", tolerance=2
        ).to_dicts()
        assert result == oracle  # distances 5 and 3 both exceed tolerance 2 -> no matches

    @pytest.mark.parametrize("backend_name", _ASOF_NULL)
    def test_asof_null_keys(self, backend_name, backend_factory):
        """Order-insensitive comparison (`sorted_dicts` by the never-null `val`
        column): DuckDB defaults to NULLS LAST on ASC, SQLite to NULLS FIRST —
        a pre-existing, orthogonal engine divergence in null-sort defaults.
        Values must still match exactly; only row position for the
        null-containing row is exempted."""
        left_data = {"t": [None, 3], "val": ["n", "b"]}
        right_data = {"t": [None, 2], "score": [99, 20]}
        oracle = self._oracle(left_data, right_data, on="t", strategy="backward")
        left, right = backend_factory.create_pair(left_data, right_data, backend_name)
        result = ma.relation(left).join_asof(right, on="t", strategy="backward").to_dicts()
        assert sorted_dicts(result, "val") == sorted_dicts(oracle, "val")
