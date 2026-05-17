"""Cross-backend result verification for string extension operations."""

from __future__ import annotations

import pytest

import mountainash as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

# -- Known divergences --
# Ibis backends: custom chars argument is silently ignored by strip_chars,
#   strip_chars_start, and strip_chars_end — only whitespace stripping works.
# Narwhals/pandas: strip_chars_start and strip_chars_end without arguments
#   strip both sides instead of only the requested side.

IBIS_BACKENDS = {"ibis-polars", "ibis-duckdb", "ibis-sqlite"}
NARWHALS_PANDAS_BACKENDS = {"pandas", "narwhals-polars", "narwhals-pandas"}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStrStripChars:
    def test_strip_whitespace(self, backend_name, backend_factory, collect_expr):
        data = {"s": ["  hello  ", " world ", "foo"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.strip_chars())
        assert actual == ["hello", "world", "foo"]

    def test_strip_custom_chars(self, backend_name, backend_factory, collect_expr):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail(
                "Ibis backends ignore custom chars argument in strip_chars; "
                "only whitespace stripping is supported."
            )
        data = {"s": ["xxhelloxx", "xworldx", "foo"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.strip_chars("x"))
        assert actual == ["hello", "world", "foo"]

    def test_strip_no_effect(self, backend_name, backend_factory, collect_expr):
        data = {"s": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.strip_chars())
        assert actual == ["hello", "world"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStrStripCharsStart:
    def test_strip_start_whitespace(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_PANDAS_BACKENDS:
            pytest.xfail(
                "Narwhals/pandas strip_chars_start() strips both sides "
                "instead of only the leading side."
            )
        data = {"s": ["  hello  ", " world"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.strip_chars_start())
        assert actual == ["hello  ", "world"]

    def test_strip_start_custom(self, backend_name, backend_factory, collect_expr):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail(
                "Ibis backends ignore custom chars argument in strip_chars_start."
            )
        data = {"s": ["xxhello", "xworld"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.strip_chars_start("x"))
        assert actual == ["hello", "world"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStrStripCharsEnd:
    def test_strip_end_whitespace(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_PANDAS_BACKENDS:
            pytest.xfail(
                "Narwhals/pandas strip_chars_end() strips both sides "
                "instead of only the trailing side."
            )
        data = {"s": ["  hello  ", "world "]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.strip_chars_end())
        assert actual == ["  hello", "world"]

    def test_strip_end_custom(self, backend_name, backend_factory, collect_expr):
        if backend_name in IBIS_BACKENDS:
            pytest.xfail(
                "Ibis backends ignore custom chars argument in strip_chars_end."
            )
        data = {"s": ["helloxx", "worldx"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.strip_chars_end("x"))
        assert actual == ["hello", "world"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStrLenChars:
    def test_len_chars_ascii(self, backend_name, backend_factory, collect_expr):
        data = {"s": ["hello", "ab", "x"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.len_chars())
        assert actual == [5, 2, 1]

    def test_len_chars_empty(self, backend_name, backend_factory, collect_expr):
        data = {"s": ["", "a", "ab"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.len_chars())
        assert actual == [0, 1, 2]

    def test_len_chars_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"s": ["hello", None, "ab"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.len_chars())
        assert actual[0] == 5
        assert actual[1] is None
        assert actual[2] == 2


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStrZfill:
    def test_zfill_basic(self, backend_name, backend_factory, collect_expr):
        data = {"s": ["42", "7", "123"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.zfill(5))
        assert actual == ["00042", "00007", "00123"]

    def test_zfill_already_wide(self, backend_name, backend_factory, collect_expr):
        data = {"s": ["12345", "123456"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.zfill(5))
        assert actual == ["12345", "123456"]


# -- Known divergences --
# Narwhals backends: strptime_date() and strptime_timestamp() are not supported.
# Ibis backends: to_date returns datetime (with time=00:00) instead of date.

NARWHALS_ALL_BACKENDS = {"pandas", "narwhals-polars", "narwhals-pandas"}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStrToDate:
    def test_to_date_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_ALL_BACKENDS:
            pytest.xfail(
                "Narwhals backend does not support strptime_date()."
            )
        import datetime

        data = {"s": ["2024-03-15", "2024-06-20"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.to_date("%Y-%m-%d"))
        expected_dates = [datetime.date(2024, 3, 15), datetime.date(2024, 6, 20)]

        # Ibis backends return datetime instead of date; compare date part only
        if backend_name in IBIS_BACKENDS:
            assert [v.date() if isinstance(v, datetime.datetime) else v for v in actual] == expected_dates
        else:
            assert actual == expected_dates

    def test_to_date_different_format(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_ALL_BACKENDS:
            pytest.xfail(
                "Narwhals backend does not support strptime_date()."
            )
        if backend_name in IBIS_BACKENDS:
            pytest.xfail(
                "Ibis backends ignore custom format strings in to_date; "
                "only ISO-8601 (YYYY-MM-DD) parsing is supported."
            )
        import datetime

        data = {"s": ["15/03/2024", "20/06/2024"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.to_date("%d/%m/%Y"))
        expected_dates = [datetime.date(2024, 3, 15), datetime.date(2024, 6, 20)]
        assert actual == expected_dates


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestStrToDatetime:
    def test_to_datetime_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_ALL_BACKENDS:
            pytest.xfail(
                "Narwhals backend does not support strptime_timestamp()."
            )
        import datetime

        data = {"s": ["2024-03-15 10:30:00", "2024-06-20 14:00:00"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.to_datetime("%Y-%m-%d %H:%M:%S"))
        expected = [
            datetime.datetime(2024, 3, 15, 10, 30),
            datetime.datetime(2024, 6, 20, 14, 0),
        ]
        assert actual == expected

    def test_to_datetime_with_seconds(self, backend_name, backend_factory, collect_expr):
        if backend_name in NARWHALS_ALL_BACKENDS:
            pytest.xfail(
                "Narwhals backend does not support strptime_timestamp()."
            )
        import datetime

        data = {"s": ["2024-01-01 00:00:00", "2024-12-31 23:59:59"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").str.to_datetime("%Y-%m-%d %H:%M:%S"))
        expected = [
            datetime.datetime(2024, 1, 1, 0, 0, 0),
            datetime.datetime(2024, 12, 31, 23, 59, 59),
        ]
        assert actual == expected
