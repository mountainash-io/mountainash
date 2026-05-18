"""Cross-backend result verification for multi-arg aggregate free functions.

Tests corr(), median(), quantile() exposed as ma.corr(), ma.median(), ma.quantile().
These use Substrait multi-arg signatures that don't yet match backend protocols —
all backends currently xfail. When a backend wires support, the xfail flips to
xpass and CI catches it.
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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestCorr:
    def test_corr_perfect_positive(self, backend_name, backend_factory):
        if backend_name != "ibis-polars":
            pytest.xfail("corr() Substrait signature not wired to this backend")
        data = {
            "g": ["a", "a", "a", "a"],
            "x": [1.0, 2.0, 3.0, 4.0],
            "y": [2.0, 4.0, 6.0, 8.0],
        }
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .group_by("g")
            .agg(ma.corr(ma.col("x"), ma.col("y")).alias("c"))
            .to_dicts()
        )
        assert result[0]["c"] == pytest.approx(1.0)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestMedian:
    @pytest.mark.xfail(
        strict=True,
        reason="median() Substrait signature (precision, x) not wired to any backend protocol",
    )
    def test_median_basic(self, backend_name, backend_factory):
        data = {"g": ["a", "a", "a"], "x": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .group_by("g")
            .agg(ma.median(ma.lit(0.5), ma.col("x")).alias("m"))
            .to_dicts()
        )
        assert result[0]["m"] == pytest.approx(2.0)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestQuantile:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "quantile() Substrait signature (boundaries, precision, n, distribution) "
            "not wired to any backend protocol"
        ),
    )
    def test_quantile_median(self, backend_name, backend_factory):
        data = {"g": ["a", "a", "a", "a", "a"], "x": [1.0, 2.0, 3.0, 4.0, 5.0]}
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .group_by("g")
            .agg(
                ma.quantile(
                    ma.lit(0.5),
                    ma.lit(0.01),
                    ma.lit(1),
                    ma.lit("linear"),
                ).alias("q")
            )
            .to_dicts()
        )
        assert result[0]["q"] == pytest.approx(3.0)


class TestFreeFunctionImports:
    def test_corr_importable(self):
        assert ma.corr is not None

    def test_median_importable(self):
        assert ma.median is not None

    def test_quantile_importable(self):
        assert ma.quantile is not None
