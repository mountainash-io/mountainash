"""Cross-backend tests for Tier 3 .str namespace operations.

Tests for: to_integer, to_time, json_decode, json_path_match,
encode, decode, extract_groups.

Backend support: to_integer(base=10) is cross-backend; all others are
Polars-only and xfail on other backends with strict=True.
"""

from __future__ import annotations

import pytest
import mountainash.expressions as ma


# ---------------------------------------------------------------------------
# Backend lists
# ---------------------------------------------------------------------------

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_ONLY = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(
        strict=True, reason="Polars-only operation — raises BackendCapabilityError on Narwhals",
    )),
    pytest.param("narwhals", marks=pytest.mark.xfail(
        strict=True, reason="Polars-only operation — raises BackendCapabilityError on Narwhals",
    )),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(
        strict=True, reason="Polars-only operation — raises BackendCapabilityError on Ibis",
    )),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
        strict=True, reason="Polars-only operation — raises BackendCapabilityError on Ibis",
    )),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(
        strict=True, reason="Polars-only operation — raises BackendCapabilityError on Ibis",
    )),
]

POLARS_ONLY_HEX = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(
        strict=True, reason="to_integer(base=16) not supported on Narwhals",
    )),
    pytest.param("narwhals", marks=pytest.mark.xfail(
        strict=True, reason="to_integer(base=16) not supported on Narwhals",
    )),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(
        strict=True, reason="to_integer(base=16) not supported on Ibis",
    )),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
        strict=True, reason="to_integer(base=16) not supported on Ibis",
    )),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(
        strict=True, reason="to_integer(base=16) not supported on Ibis",
    )),
]


# =============================================================================
# to_integer
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestToIntegerBase10:
    """to_integer(base=10) works across all backends via cast."""

    def test_to_integer_base10(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["1", "42", "100"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.to_integer()
        actual = collect_expr(df, expr)
        assert actual == [1, 42, 100], f"[{backend_name}] got {actual}"

    def test_to_integer_negative(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["-5", "0", "7"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.to_integer(base=10)
        actual = collect_expr(df, expr)
        assert actual == [-5, 0, 7], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY_HEX)
class TestToIntegerHex:
    """to_integer(base=16) is Polars-only; other backends raise BackendCapabilityError."""

    def test_to_integer_hex(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["ff", "10", "0a"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.to_integer(base=16)
        actual = collect_expr(df, expr)
        assert actual == [255, 16, 10], f"[{backend_name}] got {actual}"


# =============================================================================
# to_time (Polars-only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY)
class TestToTime:
    """to_time is Polars-only."""

    def test_to_time(self, backend_name, backend_factory, collect_expr):
        import datetime

        data = {"val": ["12:30:00", "08:15:30"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.to_time("%H:%M:%S")
        actual = collect_expr(df, expr)
        assert actual == [
            datetime.time(12, 30, 0),
            datetime.time(8, 15, 30),
        ], f"[{backend_name}] got {actual}"


# =============================================================================
# json_decode (Polars-only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY)
class TestJsonDecode:
    """json_decode is Polars-only."""

    def test_json_decode_integer(self, backend_name, backend_factory, collect_expr):
        import polars as pl

        data = {"val": ["42", "99"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.json_decode(pl.Int64)
        actual = collect_expr(df, expr)
        assert actual == [42, 99], f"[{backend_name}] got {actual}"


# =============================================================================
# json_path_match (Polars-only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY)
class TestJsonPathMatch:
    """json_path_match is Polars-only."""

    def test_json_path_match(self, backend_name, backend_factory, collect_expr):
        data = {"val": ['{"name":"alice"}', '{"name":"bob"}']}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.json_path_match("$.name")
        actual = collect_expr(df, expr)
        assert actual == ["alice", "bob"], f"[{backend_name}] got {actual}"


# =============================================================================
# encode (Polars-only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY)
class TestEncode:
    """encode is Polars-only."""

    def test_encode_hex(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["hi", "ab"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.encode("hex")
        actual = collect_expr(df, expr)
        assert actual == ["6869", "6162"], f"[{backend_name}] got {actual}"

    def test_encode_base64(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["hi"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.encode("base64")
        actual = collect_expr(df, expr)
        assert actual == ["aGk="], f"[{backend_name}] got {actual}"


# =============================================================================
# decode (Polars-only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY)
class TestDecode:
    """decode is Polars-only. Returns binary values."""

    def test_decode_hex(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["6869", "6162"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.decode("hex")
        actual = collect_expr(df, expr)
        assert actual == [b"hi", b"ab"], f"[{backend_name}] got {actual}"

    def test_decode_base64(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["aGk="]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.decode("base64")
        actual = collect_expr(df, expr)
        assert actual == [b"hi"], f"[{backend_name}] got {actual}"


# =============================================================================
# extract_groups (Polars-only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY)
class TestExtractGroups:
    """extract_groups is Polars-only. Returns struct/dict values."""

    def test_extract_groups(self, backend_name, backend_factory, collect_expr):
        data = {"val": ["foo-bar", "hello-world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.extract_groups(r"(?P<first>\w+)-(?P<second>\w+)")
        actual = collect_expr(df, expr)
        assert actual == [
            {"first": "foo", "second": "bar"},
            {"first": "hello", "second": "world"},
        ], f"[{backend_name}] got {actual}"
