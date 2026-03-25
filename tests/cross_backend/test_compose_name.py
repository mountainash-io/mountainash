"""Cross-backend tests for name operations fluent composition."""

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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeName:
    """Test .name accessor in composed expressions."""

    def test_arithmetic_then_alias(self, backend_name, backend_factory):
        """(col_a + col_b).name.alias('total') — verify column name."""
        data = {"a": [1, 2, 3], "b": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        expr = (ma.col("a") + ma.col("b")).name.alias("total")
        backend_expr = expr.compile(df)
        result = df.select(backend_expr)

        if backend_name.startswith("ibis-"):
            cols = result.columns
        elif backend_name == "pandas":
            cols = list(result.columns)
        else:
            cols = result.columns

        assert "total" in cols, f"[{backend_name}] Expected 'total' column, got {cols}"

    def test_string_upper_then_suffix(self, backend_name, backend_factory):
        """col.str.upper().name.suffix('_clean') — verify column name."""
        data = {"name": ["alice", "bob"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.upper().name.suffix("_clean")
        backend_expr = expr.compile(df)
        result = df.select(backend_expr)

        if backend_name.startswith("ibis-"):
            cols = result.columns
        elif backend_name == "pandas":
            cols = list(result.columns)
        else:
            cols = result.columns

        assert any("_clean" in c for c in cols), f"[{backend_name}] Expected column with '_clean' suffix, got {cols}"

    def test_fill_null_then_prefix(self, backend_name, backend_factory):
        """col.fill_null(0).name.prefix('filled_') — verify column name."""
        data = {"value": [1, None, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").fill_null(0).name.prefix("filled_")
        backend_expr = expr.compile(df)
        result = df.select(backend_expr)

        if backend_name.startswith("ibis-"):
            cols = result.columns
        elif backend_name == "pandas":
            cols = list(result.columns)
        else:
            cols = result.columns

        assert any("filled_" in c for c in cols), f"[{backend_name}] Expected column with 'filled_' prefix, got {cols}"
