"""Cross-backend tests for strip_prefix() and strip_suffix() (Batch 5).

strip_prefix uses AST-level composition (IfThenNode with starts_with + substring).
strip_suffix is wired as a dedicated backend method (regex-based on Narwhals/Ibis,
native str.strip_suffix on Polars).
"""

import pytest
import mountainash.expressions as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStripPrefix:
    def test_strip_prefix_present(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["prefix_hello", "prefix_world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strip_prefix("prefix_")
        actual = collect_expr(df, expr)
        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    def test_strip_prefix_absent(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["hello", "prefix_world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strip_prefix("prefix_")
        actual = collect_expr(df, expr)
        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStripSuffix:
    def test_strip_suffix_present(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["hello_suffix", "world_suffix"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strip_suffix("_suffix")
        actual = collect_expr(df, expr)
        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    def test_strip_suffix_absent(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["hello", "world_suffix"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strip_suffix("_suffix")
        actual = collect_expr(df, expr)
        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"
