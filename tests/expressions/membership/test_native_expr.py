"""Tests for build-time backend-native-expression predicate."""
from __future__ import annotations

import pytest

from mountainash.expressions.membership.native_expr import (
    is_backend_native_expression,
)


class TestIsBackendNativeExpression:
    """is_backend_native_expression detects backend-native expression objects."""

    def test_polars_expr_is_native(self) -> None:
        """pl.Expr is recognised as backend-native."""
        pytest.importorskip("polars")
        import polars as pl

        assert is_backend_native_expression(pl.col("x")) is True

    def test_narwhals_expr_is_native(self) -> None:
        """nw.Expr is recognised as backend-native."""
        pytest.importorskip("narwhals")
        import narwhals as nw

        assert is_backend_native_expression(nw.col("x")) is True

    def test_narwhals_series_is_native(self) -> None:
        """nw.Series is recognised as backend-native."""
        pytest.importorskip("narwhals")
        pytest.importorskip("polars")
        import polars as pl
        import narwhals as nw

        s = nw.from_native(pl.Series("a", [1, 2, 3]), series_only=True)
        assert is_backend_native_expression(s) is True

    def test_ibis_expr_is_native(self) -> None:
        """ibis Expr is recognised as backend-native."""
        pytest.importorskip("ibis")
        import ibis

        expr = ibis.literal(1)
        assert is_backend_native_expression(expr) is True

    def test_ibis_deferred_is_native(self) -> None:
        """ibis Deferred is recognised as backend-native."""
        pytest.importorskip("ibis")
        import ibis.common.deferred as idd

        assert is_backend_native_expression(idd.Deferred("x")) is True

    # --- False cases ---

    def test_mountainash_col_is_not_native(self) -> None:
        """ma.col('x') is NOT a native expression."""
        import mountainash as ma

        assert is_backend_native_expression(ma.col("x")) is False

    def test_scalar_int_is_not_native(self) -> None:
        """A plain integer is NOT a native expression."""
        assert is_backend_native_expression(5) is False

    def test_list_is_not_native(self) -> None:
        """A list is NOT a native expression."""
        assert is_backend_native_expression([1, 2]) is False

    def test_str_is_not_native(self) -> None:
        """A str is NOT a native expression."""
        assert is_backend_native_expression("ab") is False

    def test_bytes_is_not_native(self) -> None:
        """Bytes are NOT a native expression."""
        assert is_backend_native_expression(b"ab") is False

    def test_dict_is_not_native(self) -> None:
        """A dict is NOT a native expression."""
        assert is_backend_native_expression({"a": 1}) is False

    def test_none_is_not_native(self) -> None:
        """None is NOT a native expression."""
        assert is_backend_native_expression(None) is False

    def test_tuple_is_not_native(self) -> None:
        """A tuple is NOT a native expression."""
        assert is_backend_native_expression((1, 2)) is False

    def test_float_is_not_native(self) -> None:
        """A float is NOT a native expression."""
        assert is_backend_native_expression(3.14) is False
