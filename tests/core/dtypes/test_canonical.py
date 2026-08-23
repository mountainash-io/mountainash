# tests/core/dtypes/test_canonical.py
"""Canonical enum, alias parsing, parse_dtype/parse_cast_target."""
import datetime

import polars as pl
import pytest

from mountainash.core.dtypes.canonical import (
    MountainashDtype as D,
    NativeDtype,
    parse_cast_target,
    parse_dtype,
)
from mountainash.core.dtypes.errors import UnknownDtypeError
from mountainash.core.dtypes.targets import TypeTarget


class TestEnum:
    def test_canonical_members(self):
        # Assert the exact membership (content-based, not a magic count —
        # a bare len() check is a refactoring footgun).
        assert {m.value for m in D} == {
            "bool",
            "i8", "i16", "i32", "i64",
            "u8", "u16", "u32", "u64",
            "fp32", "fp64",
            "string", "binary",
            "date", "time", "timestamp", "duration",
            "list", "struct",
            "json", "xsd_duration", "xsd_year", "xsd_yearmonth",
        }

    def test_new_container_members(self):
        assert D.LIST.value == "list"
        assert D.STRUCT.value == "struct"

    def test_v2_semantic_string_members(self):
        # Task 2 (item 113 Unit B): semantic-string canonical types for the
        # Frictionless v2 boundary — JSON (GEOJSON), and the XSD lexical-form
        # types (duration/year/yearmonth). Physically string on every target.
        assert D.JSON.value == "json"
        assert D.XSD_DURATION.value == "xsd_duration"
        assert D.XSD_YEAR.value == "xsd_year"
        assert D.XSD_YEARMONTH.value == "xsd_yearmonth"


class TestParseDtype:
    def test_enum_identity(self):
        assert parse_dtype(D.I64) is D.I64

    @pytest.mark.parametrize("value,expected", [
        (int, D.I64), (float, D.FP64), (str, D.STRING), (bool, D.BOOL),
        (datetime.date, D.DATE), (datetime.time, D.TIME),
        (datetime.datetime, D.TIMESTAMP), (datetime.timedelta, D.DURATION),
    ])
    def test_python_types(self, value, expected):
        assert parse_dtype(value) is expected

    @pytest.mark.parametrize("value,expected", [
        ("i64", D.I64), ("Int64", D.I64), ("int64", D.I64),
        ("Utf8", D.STRING), ("f32", D.FP32), ("Datetime", D.TIMESTAMP),
        # Frictionless names folded into the alias table:
        ("integer", D.I64), ("number", D.FP64), ("datetime", D.TIMESTAMP),
        ("array", D.LIST), ("object", D.STRUCT),
        ("list", D.LIST), ("List", D.LIST), ("struct", D.STRUCT), ("Struct", D.STRUCT),
    ])
    def test_string_aliases(self, value, expected):
        assert parse_dtype(value) is expected

    def test_returns_enum_not_string(self):
        assert isinstance(parse_dtype("i64"), D)

    def test_bool_checked_before_int(self):
        assert parse_dtype(bool) is D.BOOL

    def test_unknown_string_raises(self):
        with pytest.raises(UnknownDtypeError, match="i65"):
            parse_dtype("i65")

    def test_native_object_raises_with_pointer(self):
        with pytest.raises(UnknownDtypeError, match="parse_cast_target"):
            parse_dtype(pl.Datetime("us"))

    def test_semantic_frictionless_names_are_not_aliases(self):
        # year/yearmonth/any are semantic, not structural — boundary map only
        for name in ("year", "yearmonth", "any"):
            with pytest.raises(UnknownDtypeError):
                parse_dtype(name)


class TestParseCastTarget:
    def test_canonical_passthrough(self):
        assert parse_cast_target("i64") is D.I64

    def test_native_wrapped_without_normalization(self):
        dt = pl.Datetime("us", "UTC")
        result = parse_cast_target(dt)
        assert isinstance(result, NativeDtype)
        assert result.value == dt          # parameters preserved exactly
        assert result.target is TypeTarget.POLARS

    def test_native_class_wrapped(self):
        result = parse_cast_target(pl.Int64)
        assert isinstance(result, NativeDtype)
        assert result.target is TypeTarget.POLARS

    def test_garbage_raises(self):
        with pytest.raises(UnknownDtypeError):
            parse_cast_target(object())
