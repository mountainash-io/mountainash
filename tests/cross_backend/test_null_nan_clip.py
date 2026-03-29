"""Cross-backend tests for clip(), is_not_nan(), and fill_nan().

Batch 1 remainder (clip) and Batch 2 expression-level operations (is_not_nan, fill_nan).
Table-level operations (drop_nulls, forward_fill, backward_fill) are excluded —
they are not pure expression transforms.
"""

import pytest
import mountainash_expressions as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

FLOAT_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
]


# =============================================================================
# clip()
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestClip:
    def test_clip_both_bounds(self, backend_name, backend_factory, select_and_extract):
        data = {"val": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").clip(lower=5, upper=15)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [5, 5, 10, 15, 15], f"[{backend_name}] got {actual}"

    def test_clip_lower_only(self, backend_name, backend_factory, select_and_extract):
        data = {"val": [1, 5, 10]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").clip(lower=5)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [5, 5, 10], f"[{backend_name}] got {actual}"

    def test_clip_upper_only(self, backend_name, backend_factory, select_and_extract):
        data = {"val": [1, 5, 10]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").clip(upper=5)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [1, 5, 5], f"[{backend_name}] got {actual}"

    def test_clip_no_bounds(self, backend_name, backend_factory, select_and_extract):
        data = {"val": [1, 5, 10]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").clip()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [1, 5, 10], f"[{backend_name}] got {actual}"


# =============================================================================
# is_not_nan()
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize(
    "backend_name",
    [
        "polars",
        "pandas",
        "narwhals",
        "ibis-polars",
        pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="DuckDB is_nan/is_not_nan returns NULL for non-float types")),
    ],
)
class TestIsNotNan:
    def test_is_not_nan_basic(self, backend_name, backend_factory, select_and_extract):
        data = {"val": [1.0, float("nan"), 3.0, float("nan"), 5.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_not_nan()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [True, False, True, False, True], f"[{backend_name}] got {actual}"


# =============================================================================
# fill_nan()
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize(
    "backend_name",
    [
        "polars",
        "pandas",
        "narwhals",
        "ibis-polars",
        pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="DuckDB isnan() not working correctly via ibis for fill_nan")),
    ],
)
class TestFillNan:
    def test_fill_nan_with_value(self, backend_name, backend_factory, select_and_extract):
        data = {"val": [1.0, float("nan"), 3.0, float("nan"), 5.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").fill_nan(0.0)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [1.0, 0.0, 3.0, 0.0, 5.0], f"[{backend_name}] got {actual}"
