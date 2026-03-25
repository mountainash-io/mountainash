"""Cross-backend tests for string namespace fluent composition."""

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
class TestComposeString:
    """Test fluent .str method chaining patterns."""

    def test_lower_then_contains(self, backend_name, backend_factory, get_result_count):
        """Case-insensitive search via .str.lower().str.contains()."""
        data = {"name": ["John Smith", "JOHNNY B", "Jane Doe", "johnson"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.lower().str.contains("john")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 (John Smith, JOHNNY B, johnson), got {count}"

    def test_replace_then_upper(self, backend_name, backend_factory, select_and_extract):
        """Sequential transforms: replace then uppercase."""
        data = {"code": ["a_b", "c_d", "e_f"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("code").str.replace("_", "-").str.upper()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == ["A-B", "C-D", "E-F"], f"[{backend_name}] got {actual}"

    def test_trim_then_len_then_filter(self, backend_name, backend_factory, get_result_count):
        """String to numeric to boolean: .str.trim().str.len().gt(3)."""
        data = {"name": ["  Al  ", " Bob ", " Charlotte ", "  Di  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.trim().str.len().gt(3)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 1, f"[{backend_name}] Expected 1 (Charlotte), got {count}"

    def test_negation_of_contains(self, backend_name, backend_factory, get_result_count):
        """Negation: ~col('status').str.contains('archived')."""
        data = {"status": ["active", "archived", "pending", "archived_old"]}
        df = backend_factory.create(data, backend_name)

        expr = ~ma.col("status").str.contains("archived")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 (active, pending), got {count}"

    def test_lower_then_ends_with(self, backend_name, backend_factory, get_result_count):
        """Real-world pattern: case-insensitive email domain check."""
        data = {"email": ["user@Gmail.COM", "admin@yahoo.com", "test@GMAIL.com", "x@other.org"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("email").str.lower().str.ends_with("@gmail.com")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 gmail addresses, got {count}"

    def test_three_deep_chain(self, backend_name, backend_factory, get_result_count):
        """3-deep chain: trim -> lower -> contains."""
        data = {"name": ["  Admin ", " ADMIN_USER ", "guest", "  root_admin  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").str.trim().str.lower().str.contains("admin")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 (Admin, ADMIN_USER, root_admin), got {count}"
