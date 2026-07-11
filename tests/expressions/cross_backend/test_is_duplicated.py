"""Cross-backend tests for is_duplicated (mountainash extension)."""
import pytest

import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestIsDuplicated:
    def test_is_duplicated_basic(self, backend_name, backend_factory, collect_expr):
        data = {"val": [1, 2, 2, 3, 1]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_duplicated()
        actual = collect_expr(df, expr)
        assert actual == [True, True, True, False, True], f"[{backend_name}] got {actual}"

    def test_is_duplicated_all_unique(self, backend_name, backend_factory, collect_expr):
        data = {"val": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_duplicated()
        actual = collect_expr(df, expr)
        assert actual == [False, False, False], f"[{backend_name}] got {actual}"

    def test_is_duplicated_strings(self, backend_name, backend_factory, collect_expr):
        data = {"name": ["a", "b", "a", "c"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").is_duplicated()
        actual = collect_expr(df, expr)
        assert actual == [True, False, True, False], f"[{backend_name}] got {actual}"

    def test_is_duplicated_not_for_unique_rule(self, backend_name, backend_factory, collect_expr):
        """The `unique` constraint shape: is_duplicated().not_() is True for unique rows."""
        data = {"val": [1, 2, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_duplicated().not_()
        actual = collect_expr(df, expr)
        assert actual == [True, False, False, True], f"[{backend_name}] got {actual}"
