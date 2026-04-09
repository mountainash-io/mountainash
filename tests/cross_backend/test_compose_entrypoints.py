"""Cross-backend tests for entrypoint fluent composition."""

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
class TestComposeEntrypoints:
    """Test coalesce/greatest/least with composed expressions."""

    def test_coalesce_with_string_transform(self, backend_name, backend_factory, collect_expr):
        """coalesce(trimmed phone, email, default)."""
        data = {
            "phone": ["  555-1234  ", None, "  ", None],
            "email": [None, "a@b.com", None, "c@d.com"],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.coalesce(ma.col("phone").str.trim(), ma.col("email"), ma.lit("N/A"))
        actual = collect_expr(df, expr)

        # Row 0: trimmed phone "555-1234" (non-null) -> "555-1234"
        # Row 1: phone is None, email "a@b.com" -> "a@b.com"
        # Row 2: trimmed phone is "" (non-null empty string) -> ""
        # Row 3: phone is None, email "c@d.com" -> "c@d.com"
        assert actual[0] == "555-1234", f"[{backend_name}] Row 0: {actual[0]}"
        assert actual[1] == "a@b.com", f"[{backend_name}] Row 1: {actual[1]}"
        assert actual[2] == "", f"[{backend_name}] Row 2: trimmed empty string is non-null: {actual[2]}"
        assert actual[3] == "c@d.com", f"[{backend_name}] Row 3: {actual[3]}"

    def test_greatest_with_arithmetic(self, backend_name, backend_factory, collect_expr):
        """greatest(a + 1, b * 2)."""
        data = {"a": [10, 1, 5], "b": [3, 20, 2]}
        df = backend_factory.create(data, backend_name)

        expr = ma.greatest(ma.col("a") + 1, ma.col("b") * 2)
        actual = collect_expr(df, expr)

        # Row 0: max(11, 6) = 11
        # Row 1: max(2, 40) = 40
        # Row 2: max(6, 4) = 6
        assert actual == [11, 40, 6], f"[{backend_name}] got {actual}"

    def test_least_with_null_handling(self, backend_name, backend_factory, collect_expr):
        """least(x, y.fill_null(999))."""
        data = {"x": [10, 50, 30], "y": [5, None, 20]}
        df = backend_factory.create(data, backend_name)

        expr = ma.least(ma.col("x"), ma.col("y").fill_null(ma.lit(999)))
        actual = collect_expr(df, expr)

        # Row 0: min(10, 5) = 5
        # Row 1: min(50, 999) = 50
        # Row 2: min(30, 20) = 20
        assert actual == [5, 50, 20], f"[{backend_name}] got {actual}"

    def test_coalesce_then_compare(self, backend_name, backend_factory, get_result_count):
        """coalesce(a, b) > 0 — entrypoint then comparison."""
        data = {"a": [None, 5, None, -3], "b": [10, None, -1, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.coalesce(ma.col("a"), ma.col("b")).gt(0)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: coalesce(None, 10) = 10 > 0 yes
        # Row 1: coalesce(5, None) = 5 > 0 yes
        # Row 2: coalesce(None, -1) = -1 > 0 no
        # Row 3: coalesce(-3, None) = -3 > 0 no
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"
