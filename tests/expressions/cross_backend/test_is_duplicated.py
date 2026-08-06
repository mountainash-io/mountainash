"""Cross-backend tests for is_duplicated (mountainash extension).

Known divergences:
- ibis-polars: No translation rule for WindowFunction (documented Ibis-Polars
  backend limitation — is_duplicated compiles to a per-value window count on
  Ibis; see test_window_results.py for the same divergence on rank()).
- ibis-duckdb/ibis-sqlite: the window-based is_duplicated computation does not
  guarantee input row order is preserved, so results are compared via an
  explicit ``idx`` sort key rather than raw positional equality (mirrors the
  ``.sort("group", "score")`` pattern in test_window_results.py's rank tests).
"""
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence


def _collect_ordered(df, expr):
    """Collect an expression's values, sorted by an explicit ``idx`` column.

    is_duplicated compiles to a window function on Ibis, and some Ibis SQL
    backends (sqlite) do not guarantee row order is preserved through a
    window computation. Sorting by an explicit index column makes the
    comparison order-independent without weakening what is asserted.
    """
    result = (
        ma.relation(df)
        .select(ma.col("idx"), expr.alias("result"))
        .sort("idx")
        .to_dict()
    )
    return result["result"]


_IS_DUP_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("IB-WIN-01", backend=b)) for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _IS_DUP_BACKENDS)
class TestIsDuplicated:
    def test_is_duplicated_basic(self, backend_name, backend_factory):
        data = {"idx": [0, 1, 2, 3, 4], "val": [1, 2, 2, 3, 1]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_duplicated()
        actual = _collect_ordered(df, expr)
        assert actual == [True, True, True, False, True], f"[{backend_name}] got {actual}"

    def test_is_duplicated_all_unique(self, backend_name, backend_factory):
        data = {"idx": [0, 1, 2], "val": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_duplicated()
        actual = _collect_ordered(df, expr)
        assert actual == [False, False, False], f"[{backend_name}] got {actual}"

    def test_is_duplicated_strings(self, backend_name, backend_factory):
        data = {"idx": [0, 1, 2, 3], "name": ["a", "b", "a", "c"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").is_duplicated()
        actual = _collect_ordered(df, expr)
        assert actual == [True, False, True, False], f"[{backend_name}] got {actual}"

    def test_is_duplicated_not_for_unique_rule(self, backend_name, backend_factory):
        """The `unique` constraint shape: is_duplicated().not_() is True for unique rows."""
        data = {"idx": [0, 1, 2, 3], "val": [1, 2, 2, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_duplicated().not_()
        actual = _collect_ordered(df, expr)
        assert actual == [True, False, False, True], f"[{backend_name}] got {actual}"

    def test_is_duplicated_nulls_are_duplicates(self, backend_name, backend_factory):
        """Repeated NULLs are duplicates on ALL backends (consistency-guarantees)."""
        data = {"idx": [0, 1, 2], "name": ["a", None, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("name").is_duplicated()
        actual = _collect_ordered(df, expr)
        assert actual == [False, True, True], f"[{backend_name}] got {actual}"
