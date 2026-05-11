"""Cross-backend tests for bitwise operations."""
from __future__ import annotations

import pytest

import mountainash as ma


BITWISE_BACKENDS = [
    "polars",
    "narwhals-polars",
    "ibis-duckdb",
]

BITWISE_XOR_BACKENDS = [
    "polars",
    pytest.param("narwhals-polars", marks=pytest.mark.xfail(
        strict=True,
        raises=Exception,
        reason="Narwhals does not support bitwise_xor",
    )),
    "ibis-duckdb",
]

SHIFT_BACKENDS_IBIS_ONLY = [
    pytest.param("polars", marks=pytest.mark.xfail(
        strict=True,
        raises=Exception,
        reason="Polars does not support bitwise shift operations",
    )),
    pytest.param("narwhals-polars", marks=pytest.mark.xfail(
        strict=True,
        raises=Exception,
        reason="Narwhals does not support bitwise shift operations",
    )),
    "ibis-duckdb",
]

SHIFT_UNSIGNED_BACKENDS = [
    pytest.param("polars", marks=pytest.mark.xfail(
        strict=True,
        raises=Exception,
        reason="No backend supports shift_right_unsigned",
    )),
    pytest.param("narwhals-polars", marks=pytest.mark.xfail(
        strict=True,
        raises=Exception,
        reason="No backend supports shift_right_unsigned",
    )),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
        strict=True,
        raises=Exception,
        reason="No backend supports shift_right_unsigned",
    )),
]


@pytest.mark.parametrize("backend_name", BITWISE_BACKENDS)
class TestBitwiseAnd:
    def test_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, 3, 12], "b": [3, 7, 4]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").bitwise_and(ma.col("b")))
        assert result == [1, 3, 4]

    def test_with_literal(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, 3, 12]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").bitwise_and(3))
        assert result == [1, 3, 0]


@pytest.mark.parametrize("backend_name", BITWISE_BACKENDS)
class TestBitwiseOr:
    def test_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, 3, 12], "b": [3, 7, 4]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").bitwise_or(ma.col("b")))
        assert result == [7, 7, 12]


@pytest.mark.parametrize("backend_name", BITWISE_XOR_BACKENDS)
class TestBitwiseXor:
    def test_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, 3, 12], "b": [3, 7, 4]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").bitwise_xor(ma.col("b")))
        assert result == [6, 4, 8]


@pytest.mark.parametrize("backend_name", BITWISE_BACKENDS)
class TestBitwiseNot:
    def test_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, 3, 12]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").bitwise_not())
        assert result == [-6, -4, -13]


@pytest.mark.parametrize("backend_name", SHIFT_BACKENDS_IBIS_ONLY)
class TestShiftLeft:
    def test_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3], "b": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").shift_left(ma.col("b")))
        assert result == [2, 8, 24]

    def test_with_literal(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").shift_left(2))
        assert result == [4, 8, 12]


@pytest.mark.parametrize("backend_name", SHIFT_BACKENDS_IBIS_ONLY)
class TestShiftRight:
    def test_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [8, 16, 24], "b": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").shift_right(ma.col("b")))
        assert result == [4, 4, 3]


@pytest.mark.parametrize("backend_name", SHIFT_UNSIGNED_BACKENDS)
class TestShiftRightUnsigned:
    def test_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [8, 16, 24]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("a").shift_right_unsigned(1))
        assert result == [4, 8, 12]
