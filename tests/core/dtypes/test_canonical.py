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



class TestParseDtype:
    @pytest.mark.parametrize("precision,scale", [(1, 0), (38, 0), (38, 38), (20, 3)])
    def test_decimal_descriptor_accepts_domain_edges(self, precision, scale):
        from mountainash.core.dtypes.canonical import DecimalDtype

        dtype = DecimalDtype(precision=precision, scale=scale)
        assert dtype.precision == precision
        assert dtype.scale == scale

    @pytest.mark.parametrize(
        "values",
        [
            {"precision": 0, "scale": 0},
            {"precision": 39, "scale": 0},
            {"precision": 4, "scale": 5},
            {"precision": True, "scale": 0},
            {"precision": 4, "scale": False},
            {"precision": 4.0, "scale": 0},
            {"precision": "4", "scale": 0},
            {"precision": 4, "scale": 1, "extra": 1},
        ],
    )
    def test_decimal_descriptor_rejects_invalid_parameters(self, values):
        from pydantic import ValidationError

        from mountainash.core.dtypes.canonical import DecimalDtype

        with pytest.raises(ValidationError):
            DecimalDtype(**values)

    def test_decimal_descriptor_is_frozen(self):
        from pydantic import ValidationError

        from mountainash.core.dtypes.canonical import DecimalDtype

        dtype = DecimalDtype(precision=20, scale=3)
        with pytest.raises(ValidationError):
            dtype.precision = 21
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

    def test_decimal_descriptor_parses_as_canonical_dtype(self):
        from mountainash.core.dtypes.canonical import DecimalDtype

        dtype = DecimalDtype(precision=20, scale=3)
        assert parse_dtype(dtype) is dtype

    def test_bare_decimal_is_rejected_as_cast_target(self):
        with pytest.raises(UnknownDtypeError, match="precision"):
            parse_cast_target(D.DECIMAL)

    def test_lexical_kind_aliases_parse(self):
        assert parse_dtype("lexical_integer") is D.LEXICAL_INTEGER
        assert parse_dtype("lexical_decimal") is D.LEXICAL_DECIMAL

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
