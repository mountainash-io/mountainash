"""Cross-backend result verification for join operations.

Phase 2 of the relation result verification suite. Tests inner, left, right,
outer, semi, anti, cross joins, suffix disambiguation, multi-key joins, and
join_asof across all 7 backends.
"""
from __future__ import annotations

import pytest

import mountainash as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


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
        if backend_name in ("ibis-polars", "ibis-duckdb", "ibis-sqlite"):
            pytest.xfail(
                "Ibis backend uses suffix as standalone column name (e.g. '_r') "
                "rather than appending it to the original name (e.g. 'val_r')"
            )
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
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestJoinAsof:
    def test_asof_backward_strategy(self, backend_name, backend_factory):
        """Test asof join with backward strategy.

        join_asof matches each left row with the nearest right row where
        right.on <= left.on (backward strategy).

        Note: The `by` parameter is silently dropped by the Relation API
        (JoinRelNode has no `by` field, visitor hardcodes by=None).
        This is a known mountainash bug — we test without `by` here.
        """
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail(
                "mountainash narwhals backend passes unsupported 'tolerance' kwarg "
                "to DataFrame.join_asof() — known backend bug"
            )
        if backend_name == "ibis-sqlite":
            pytest.xfail("ASOF joins are not supported by SQLite via Ibis")
        if backend_name == "ibis-duckdb":
            pytest.xfail(
                "ibis-duckdb asof join does not preserve left-side row order"
            )
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
