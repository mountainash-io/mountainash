"""Cross-backend tests for the 9 fluent aggregate reducers."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations import relation


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


def _agg(df, expr_factory):
    """Group by 'g', aggregate 'x' with expr_factory, sort by 'g', return dict."""
    return (
        relation(df)
        .group_by("g")
        .agg(expr_factory(ma.col("x")).alias("v"))
        .sort("g")
        .to_dict()
    )


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestFluentReducers:
    def _df(self, backend_name, backend_factory):
        return backend_factory.create(
            {"g": ["a", "a", "a", "b", "b"], "x": [1, 2, 3, 4, 6]},
            backend_name,
        )

    def test_sum(self, backend_name, backend_factory):
        result = _agg(self._df(backend_name, backend_factory), lambda c: c.sum())
        assert result["v"] == [6, 10], f"[{backend_name}]"

    def test_avg(self, backend_name, backend_factory):
        result = _agg(self._df(backend_name, backend_factory), lambda c: c.avg())
        assert result["v"] == pytest.approx([2.0, 5.0]), f"[{backend_name}]"

    def test_min(self, backend_name, backend_factory):
        result = _agg(self._df(backend_name, backend_factory), lambda c: c.min())
        assert result["v"] == [1, 4], f"[{backend_name}]"

    def test_max(self, backend_name, backend_factory):
        result = _agg(self._df(backend_name, backend_factory), lambda c: c.max())
        assert result["v"] == [3, 6], f"[{backend_name}]"

    def test_product(self, backend_name, backend_factory):
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis backends have no standard SQL product aggregate")
        result = _agg(self._df(backend_name, backend_factory), lambda c: c.product())
        # narwhals computes product via exp(sum(log(x))) which introduces float error
        assert result["v"] == pytest.approx([6, 24]), f"[{backend_name}]"

    def test_std_dev(self, backend_name, backend_factory):
        result = _agg(self._df(backend_name, backend_factory), lambda c: c.std_dev())
        assert result["v"][0] == pytest.approx(1.0), f"[{backend_name}]"
        assert result["v"][1] == pytest.approx(1.4142135623730951), f"[{backend_name}]"

    def test_variance(self, backend_name, backend_factory):
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail("Narwhals variance uses x.std().pow() which fails — nw.Expr has no .pow() method")
        result = _agg(self._df(backend_name, backend_factory), lambda c: c.variance())
        assert result["v"][0] == pytest.approx(1.0), f"[{backend_name}]"
        assert result["v"][1] == pytest.approx(2.0), f"[{backend_name}]"

    def test_mode(self, backend_name, backend_factory):
        if backend_name.startswith("ibis-"):
            pytest.xfail("Ibis backends have no standard SQL mode aggregate")
        if backend_name in ("pandas", "narwhals-polars", "narwhals-pandas"):
            pytest.xfail("Narwhals backend does not implement mode()")
        df = backend_factory.create(
            {"g": ["a", "a", "a", "b"], "x": [1, 1, 2, 5]},
            backend_name,
        )
        result = _agg(df, lambda c: c.mode())
        a_val = result["v"][0]
        b_val = result["v"][1]
        if isinstance(a_val, list):
            assert 1 in a_val, f"[{backend_name}]"
            assert 5 in b_val, f"[{backend_name}]"
        else:
            assert a_val == 1, f"[{backend_name}]"
            assert b_val == 5, f"[{backend_name}]"

    def test_any_value(self, backend_name, backend_factory):
        result = _agg(self._df(backend_name, backend_factory), lambda c: c.any_value())
        assert result["v"][0] in {1, 2, 3}, f"[{backend_name}]"
        assert result["v"][1] in {4, 6}, f"[{backend_name}]"

    def test_mean_alias_for_avg(self, backend_name, backend_factory):
        df = self._df(backend_name, backend_factory)
        avg_result = _agg(df, lambda c: c.avg())
        mean_result = _agg(df, lambda c: c.mean())
        assert avg_result["v"] == mean_result["v"], f"[{backend_name}]"
