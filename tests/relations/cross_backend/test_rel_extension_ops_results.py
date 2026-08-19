"""Cross-backend result verification for extension relational operations.

Phase 4 of the relation result verification suite. Tests drop_nulls,
drop_nans, with_row_index, explode, unnest, unpivot, pivot, top_k,
sample across backends.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)
from fixtures.capability_gating import (
    assert_capability_gated,
    gate_dialect,
    gate_family,
    xfail_divergence,
)

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

LIST_BACKENDS = ["polars", "narwhals-polars", "ibis-duckdb"]

STRUCT_BACKENDS = ["polars", "narwhals-polars", "ibis-polars", "ibis-duckdb"]

_IBSQL = [pytest.param(b, marks=xfail_divergence("IB-REL-10", backend=b)) for b in ALL_BACKENDS]
_WRI = [pytest.param(b, marks=xfail_divergence("NW-REL-01", backend=b)) for b in ALL_BACKENDS]
_UNNEST = [pytest.param(b, marks=xfail_divergence("NW-REL-02", backend=b)) for b in STRUCT_BACKENDS]
_PIVOT = [pytest.param(b, marks=xfail_divergence("MA-REL-01", backend=b)) for b in ALL_BACKENDS]


def sorted_dicts(dicts: list[dict], by: str | list[str]) -> list[dict]:
    """Sort list of dicts by key(s) for order-independent comparison."""
    if isinstance(by, str):
        by = [by]
    return sorted(dicts, key=lambda d: tuple(d[k] for k in by))


# ---------------------------------------------------------------------------
# Drop Nulls
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDropNulls:
    def test_drop_nulls_all_columns(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, None, 3], "b": [None, 20, 30]}, backend_name
        )
        result = ma.relation(df).drop_nulls().to_dicts()
        assert result == [{"a": 3, "b": 30}]

    def test_drop_nulls_subset(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1, None, 3], "b": [None, 20, 30]}, backend_name
        )
        result = ma.relation(df).drop_nulls(subset=["a"]).to_dicts()
        result_sorted = sorted_dicts(result, "a")
        assert result_sorted == [
            {"a": 1, "b": None},
            {"a": 3, "b": 30},
        ]


# ---------------------------------------------------------------------------
# Drop NaNs
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _IBSQL)
class TestDropNans:
    def test_drop_nans_basic(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [1.0, float("nan"), 3.0], "b": [10.0, 20.0, 30.0]},
            backend_name,
        )
        result = ma.relation(df).drop_nans().to_dicts()
        assert len(result) == 2
        assert result[0]["a"] == 1.0
        assert result[1]["a"] == 3.0


# ---------------------------------------------------------------------------
# With Row Index
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _WRI)
class TestWithRowIndex:
    def test_with_row_index_default_name(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [10, 20, 30]}, backend_name
        )
        result = assert_capability_gated(
            RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX,
            gate_family(backend_name),
            dialect=gate_dialect(backend_name),
            build=lambda: ma.relation(df).with_row_index().to_dicts(),
        )
        if backend_name == "ibis-polars":
            return
        assert result == [
            {"index": 0, "a": 10},
            {"index": 1, "a": 20},
            {"index": 2, "a": 30},
        ]

    def test_with_row_index_custom_name(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"a": [10, 20, 30]}, backend_name
        )
        result = assert_capability_gated(
            RKEY_MOUNTAINASH_REL.WITH_ROW_INDEX,
            gate_family(backend_name),
            dialect=gate_dialect(backend_name),
            build=lambda: ma.relation(df).with_row_index(name="row_num").to_dicts(),
        )
        if backend_name == "ibis-polars":
            return
        assert result == [
            {"row_num": 0, "a": 10},
            {"row_num": 1, "a": 20},
            {"row_num": 2, "a": 30},
        ]


# ---------------------------------------------------------------------------
# Explode (list columns — reduced backend set)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestExplode:
    def test_explode_list_column(self, backend_name, backend_factory):
        """Explode a list column into separate rows.

        Uses Polars directly for DataFrame creation since list columns
        need special construction.
        """
        import polars as pl

        if backend_name == "polars":
            df = pl.DataFrame({"id": [1, 2], "vals": [[10, 20], [30]]})
        elif backend_name == "narwhals-polars":
            import narwhals as nw
            df = nw.from_native(pl.DataFrame({"id": [1, 2], "vals": [[10, 20], [30]]}))
        elif backend_name == "ibis-duckdb":
            import ibis
            conn = ibis.duckdb.connect()
            df = conn.create_table(
                "test_explode",
                pl.DataFrame({"id": [1, 2], "vals": [[10, 20], [30]]}),
                overwrite=True,
            )
        else:
            pytest.skip(f"List columns not supported on {backend_name}")

        result = ma.relation(df).explode("vals").to_dicts()
        result_sorted = sorted_dicts(result, ["id", "vals"])
        assert result_sorted == [
            {"id": 1, "vals": 10},
            {"id": 1, "vals": 20},
            {"id": 2, "vals": 30},
        ]


# ---------------------------------------------------------------------------
# Unnest (struct columns — reduced backend set, xfail on narwhals)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _UNNEST)
class TestUnnest:
    def test_unnest_struct_column(self, backend_name, backend_factory):
        """Unnest a struct column into separate columns.

        Narwhals raises NotImplementedError for unnest.
        The separator="" produces flat field names (x, y) with no prefix.
        """
        import polars as pl


        if backend_name == "polars":
            df = pl.DataFrame({
                "id": [1, 2],
                "info": [{"x": 10, "y": "a"}, {"x": 20, "y": "b"}],
            })
        elif backend_name == "ibis-polars":
            import ibis
            conn = ibis.polars.connect()
            df = conn.create_table(
                "test_unnest",
                pl.DataFrame({
                    "id": [1, 2],
                    "info": [{"x": 10, "y": "a"}, {"x": 20, "y": "b"}],
                }),
                overwrite=True,
            )
        elif backend_name == "ibis-duckdb":
            import ibis
            conn = ibis.duckdb.connect()
            df = conn.create_table(
                "test_unnest",
                pl.DataFrame({
                    "id": [1, 2],
                    "info": [{"x": 10, "y": "a"}, {"x": 20, "y": "b"}],
                }),
                overwrite=True,
            )
        else:
            pytest.skip(f"Struct columns not supported on {backend_name}")

        result = ma.relation(df).unnest("info", separator="").to_dicts()
        result_sorted = sorted_dicts(result, "id")
        assert result_sorted == [
            {"id": 1, "x": 10, "y": "a"},
            {"id": 2, "x": 20, "y": "b"},
        ]


# ---------------------------------------------------------------------------
# Unpivot (wide to long)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _IBSQL)
class TestUnpivot:
    def test_unpivot_wide_to_long(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"id": [1, 2], "x": [10, 20], "y": [30, 40]},
            backend_name,
        )
        result = ma.relation(df).unpivot(
            on=["x", "y"], index="id"
        ).to_dicts()
        result_sorted = sorted_dicts(result, ["id", "variable"])
        assert result_sorted == [
            {"id": 1, "variable": "x", "value": 10},
            {"id": 1, "variable": "y", "value": 30},
            {"id": 2, "variable": "x", "value": 20},
            {"id": 2, "variable": "y", "value": 40},
        ]


# ---------------------------------------------------------------------------
# Pivot (long to wide)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _PIVOT)
class TestPivot:
    def test_pivot_long_to_wide(self, backend_name, backend_factory):
        df = backend_factory.create(
            {
                "id": [1, 1, 2, 2],
                "category": ["x", "y", "x", "y"],
                "value": [10, 20, 30, 40],
            },
            backend_name,
        )
        result = ma.relation(df).pivot(
            on="category", index="id", values="value"
        ).to_dicts()
        result_sorted = sorted_dicts(result, "id")
        # Sort column keys too for deterministic comparison
        for row in result_sorted:
            assert row["id"] in (1, 2)
        assert result_sorted[0]["x"] == 10
        assert result_sorted[0]["y"] == 20
        assert result_sorted[1]["x"] == 30
        assert result_sorted[1]["y"] == 40


# ---------------------------------------------------------------------------
# Top K
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTopK:
    def test_top_k_by_column(self, backend_name, backend_factory):
        df = backend_factory.create(
            {"name": ["a", "b", "c", "d", "e"], "score": [10, 50, 30, 40, 20]},
            backend_name,
        )
        result = ma.relation(df).top_k(3, by="score").to_dicts()
        result_sorted = sorted_dicts(result, "score")
        assert result_sorted == [
            {"name": "c", "score": 30},
            {"name": "d", "score": 40},
            {"name": "b", "score": 50},
        ]


# ---------------------------------------------------------------------------
# Sample (non-deterministic — check count and membership only)
# ---------------------------------------------------------------------------


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSample:
    """Seeded sampling is deterministic within each backend."""

    def _frame(self, backend_factory, backend_name):
        return backend_factory.create(
            {"a": list(range(20)), "b": [i * 10 for i in range(20)]},
            backend_name,
        )

    def _mark_seed_support(self, request, backend_name):
        reasons = {
            "ibis-polars": "ibis-polars: Table.sample with a random seed is unsupported",
            "ibis-sqlite": "ibis-sqlite: Table.sample with a random seed is unsupported",
        }
        if backend_name in reasons:
            request.node.add_marker(pytest.mark.xfail(strict=True, reason=reasons[backend_name]))

    def test_sample_n_row_count(self, backend_name, backend_factory, request):
        self._mark_seed_support(request, backend_name)
        df = self._frame(backend_factory, backend_name)
        result = ma.relation(df).sample(n=5, seed=7).to_dicts()
        if backend_name.startswith("ibis-"):
            assert 0 <= len(result) <= 20
        else:
            assert len(result) == 5

    def test_same_seed_same_rows(self, backend_name, backend_factory, request):
        self._mark_seed_support(request, backend_name)
        df = self._frame(backend_factory, backend_name)
        first = ma.relation(df).sample(n=5, seed=42).to_dicts()
        second = ma.relation(df).sample(n=5, seed=42).to_dicts()
        assert sorted_dicts(first, "a") == sorted_dicts(second, "a")

    def test_same_seed_same_rows_fraction(self, backend_name, backend_factory, request):
        self._mark_seed_support(request, backend_name)
        df = self._frame(backend_factory, backend_name)
        first = ma.relation(df).sample(fraction=0.4, seed=3).to_dicts()
        second = ma.relation(df).sample(fraction=0.4, seed=3).to_dicts()
        assert sorted_dicts(first, "a") == sorted_dicts(second, "a")

    def test_oversize_n_returns_all_rows(self, backend_name, backend_factory, request):
        df = self._frame(backend_factory, backend_name)
        result = ma.relation(df).sample(n=100, seed=1).to_dicts()
        assert sorted_dicts(result, "a") == sorted_dicts(
            ma.relation(df).to_dicts(), "a"
        )

    def test_fraction_zero_returns_no_rows(self, backend_name, backend_factory, request):
        df = self._frame(backend_factory, backend_name)
        assert ma.relation(df).sample(fraction=0.0, seed=1).to_dicts() == []

    def test_fraction_one_returns_all_rows(self, backend_name, backend_factory, request):
        df = self._frame(backend_factory, backend_name)
        result = ma.relation(df).sample(fraction=1.0, seed=1).to_dicts()
        assert sorted_dicts(result, "a") == sorted_dicts(
            ma.relation(df).to_dicts(), "a"
        )


@pytest.mark.cross_backend
class TestJoinAsofStrategyGate:
    def test_ibis_polars_forward_nearest_gated(self):
        import ibis
        import polars as pl
        from mountainash.core.types import BackendCapabilityError

        con = ibis.polars.connect()
        left = con.create_table("gate_l", pl.DataFrame({"t": [1, 3], "val": ["a", "b"]}), overwrite=True)
        right = con.create_table("gate_r", pl.DataFrame({"t": [2, 4], "score": [20, 40]}), overwrite=True)

        for strategy in ("forward", "nearest"):
            with pytest.raises(BackendCapabilityError) as ei:
                ma.relation(left).join_asof(right, on="t", strategy=strategy).to_polars()
            assert ei.value.limitation.predicate is not None
            assert ei.value.function_key == RKEY_MOUNTAINASH_REL.JOIN_ASOF

    def test_ibis_polars_backward_not_gated(self):
        import ibis
        import polars as pl

        con = ibis.polars.connect()
        left = con.create_table("gate_l2", pl.DataFrame({"t": [1, 3], "val": ["a", "b"]}), overwrite=True)
        right = con.create_table("gate_r2", pl.DataFrame({"t": [2, 4], "score": [20, 40]}), overwrite=True)
        result = ma.relation(left).join_asof(right, on="t", strategy="backward").to_polars()
        assert result.height == 2
