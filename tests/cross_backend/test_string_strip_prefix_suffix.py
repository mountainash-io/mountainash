"""Cross-backend tests for strip_prefix() and strip_suffix() (Batch 5).

These are AST-level composition methods using IfThenNode.
strip_prefix works on all backends (simple starts_with + substring).
strip_suffix requires cross-category AST (char_length + subtract + substring)
which only Polars handles correctly.
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

POLARS_AND_IBIS = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="narwhals str.slice does not accept expression-typed length")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals str.slice does not accept expression-typed length")),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis Polars backend does not support columnar substr args")),
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStripPrefix:
    def test_strip_prefix_present(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["prefix_hello", "prefix_world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strip_prefix("prefix_")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    def test_strip_prefix_absent(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello", "prefix_world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strip_prefix("prefix_")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_AND_IBIS)
class TestStripSuffix:
    def test_strip_suffix_present(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello_suffix", "world_suffix"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strip_suffix("_suffix")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    def test_strip_suffix_absent(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello", "world_suffix"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strip_suffix("_suffix")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"
