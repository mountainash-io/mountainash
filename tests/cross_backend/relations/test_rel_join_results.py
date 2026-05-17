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
