"""Cross-backend tests for set operations fluent composition."""

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
class TestComposeSet:
    """Test is_in/is_not_in composed with other operations."""

    def test_is_in_and_comparison(self, backend_name, backend_factory, get_result_count):
        """Set membership + comparison: status in [active, pending] AND score > 50."""
        data = {
            "status": ["active", "archived", "pending", "active", "deleted"],
            "score": [80, 90, 40, 60, 70],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("status").is_in(["active", "pending"]).and_(ma.col("score").gt(50))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # active/80 yes, archived no, pending/40 score too low, active/60 yes, deleted no
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"

    def test_is_not_in_filter(self, backend_name, backend_factory, get_result_count):
        """Exclusion: category NOT IN [archived, deleted]."""
        data = {"category": ["active", "archived", "pending", "deleted", "draft"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("category").is_not_in(["archived", "deleted"])
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 (active, pending, draft), got {count}"

    def test_string_transform_then_is_in(self, backend_name, backend_factory, get_result_count):
        """String transform then set: .str.lower().is_in(['admin', 'root'])."""
        data = {"role": ["Admin", "USER", "Root", "GUEST", "admin"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("role").str.lower().is_in(["admin", "root"])
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Admin->admin yes, USER->user no, Root->root yes, GUEST->guest no, admin yes
        assert count == 3, f"[{backend_name}] Expected 3, got {count}"

    def test_is_in_or_is_null(self, backend_name, backend_factory, get_result_count):
        """Set + null: value in [1,2,3] OR value is null."""
        data = {"value": [1, 5, None, 2, 10, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").is_in([1, 2, 3]).or_(ma.col("value").is_null())
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 1 yes, 5 no, None yes, 2 yes, 10 no, None yes
        assert count == 4, f"[{backend_name}] Expected 4, got {count}"
