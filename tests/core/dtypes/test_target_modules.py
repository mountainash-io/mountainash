# tests/core/dtypes/test_target_modules.py
"""Per-target mapping module behaviour (representative cases; the exhaustive
product is covered by test_completeness.py)."""
import polars as pl
import pytest

from mountainash.core.dtypes.canonical import MountainashDtype as D
from mountainash.core.dtypes.errors import UnknownDtypeError
from mountainash.core.dtypes import (
    target_ibis,
    target_narwhals,
    target_pandas,
    target_polars,
    target_pyarrow,
    target_python,
)


class TestPolars:
    def test_schema_types(self):
        assert target_polars.SCHEMA_TYPES[D.I64] is pl.Int64
        assert target_polars.SCHEMA_TYPES[D.LIST] is pl.List
        assert target_polars.SCHEMA_TYPES[D.STRUCT] is pl.Struct

    def test_cast_unsupported(self):
        assert target_polars.CAST_UNSUPPORTED == frozenset({D.LIST, D.STRUCT})

    @pytest.mark.parametrize("native,expected", [
        (pl.Int32, D.I32),
        (pl.Int32(), D.I32),
        (pl.Datetime("us", "UTC"), D.TIMESTAMP),   # parameterized -> base
        (pl.Categorical, D.STRING),
        (pl.List(pl.Int64), D.LIST),
        (pl.Struct({"a": pl.Int64}), D.STRUCT),
    ])
    def test_from_native(self, native, expected):
        assert target_polars.from_native(native) is expected

    def test_from_native_null_is_untyped(self):
        assert target_polars.from_native(pl.Null) is None

    def test_from_native_unknown_raises(self):
        with pytest.raises(UnknownDtypeError):
            target_polars.from_native("NotARealDtype")

    def test_parse_type_string_bare_name(self):
        assert target_polars.parse_type_string("Int32") is pl.Int32

    def test_parse_type_string_parameterized_returns_none(self):
        assert target_polars.parse_type_string("Datetime(time_unit='us', time_zone=None)") is None


class TestPandas:
    def test_schema_types_are_strings(self):
        assert target_pandas.SCHEMA_TYPES[D.I64] == "Int64"
        assert target_pandas.SCHEMA_TYPES[D.STRING] == "string"

    @pytest.mark.parametrize("name,expected", [
        ("int32", D.I32), ("Int32", D.I32), ("uint8", D.U8),
        ("float64", D.FP64), ("float16", D.FP32),
        ("datetime64[ns]", D.TIMESTAMP), ("datetime64[ns, UTC]", D.TIMESTAMP),
        ("timedelta64[ns]", D.DURATION), ("period[M]", D.TIMESTAMP),
        ("object", D.STRING), ("category", D.STRING), ("bool", D.BOOL),
    ])
    def test_from_native_strings(self, name, expected):
        assert target_pandas.from_native(name) is expected

    def test_from_native_numpy_dtype_object(self):
        import numpy as np
        assert target_pandas.from_native(np.dtype("int64")) is D.I64


class TestPyArrow:
    def test_from_native(self):
        import pyarrow as pa
        assert target_pyarrow.from_native(pa.int64()) is D.I64
        assert target_pyarrow.from_native(pa.timestamp("ns")) is D.TIMESTAMP
        assert target_pyarrow.from_native(pa.list_(pa.int64())) is D.LIST
        assert target_pyarrow.from_native(pa.large_string()) is D.STRING
        assert target_pyarrow.from_native(pa.null()) is None

    def test_parse_type_string_uses_alias(self):
        import pyarrow as pa
        assert target_pyarrow.parse_type_string("int64") == pa.int64()
        assert target_pyarrow.parse_type_string("not_a_type") is None


class TestIbis:
    @pytest.mark.parametrize("name,expected", [
        ("int64", D.I64), ("!int64", D.I64),
        ("timestamp", D.TIMESTAMP), ("timestamp('UTC')", D.TIMESTAMP),
        ("interval", D.DURATION), ("array<int64>", D.LIST),
        ("struct<a: int64>", D.STRUCT),
    ])
    def test_from_native_strings(self, name, expected):
        assert target_ibis.from_native(name) is expected

    def test_from_native_dtype_object(self):
        import ibis.expr.datatypes as dt
        assert target_ibis.from_native(dt.int32) is D.I32

    def test_parse_type_string_validates(self):
        assert target_ibis.parse_type_string("decimal(38, 9)") == "decimal(38, 9)"
        assert target_ibis.parse_type_string("not a type") is None


class TestNarwhals:
    def test_from_native(self):
        import narwhals as nw
        assert target_narwhals.from_native(nw.Int64) is D.I64
        assert target_narwhals.from_native(nw.Datetime) is D.TIMESTAMP

    def test_schema_types(self):
        import narwhals as nw
        assert target_narwhals.SCHEMA_TYPES[D.I64] is nw.Int64


class TestPython:
    def test_schema_types(self):
        import datetime
        assert target_python.SCHEMA_TYPES[D.I64] is int
        assert target_python.SCHEMA_TYPES[D.TIMESTAMP] is datetime.datetime
        assert target_python.SCHEMA_TYPES[D.LIST] is list
        assert target_python.SCHEMA_TYPES[D.STRUCT] is dict

    def test_from_native_typing_generics(self):
        from typing import Dict, List
        assert target_python.from_native(List[str]) is D.LIST
        assert target_python.from_native(list[int]) is D.LIST
        assert target_python.from_native(Dict[str, int]) is D.STRUCT

    def test_from_native_hint_strings(self):
        assert target_python.from_native("str") is D.STRING
        assert target_python.from_native("timedelta") is D.DURATION

    def test_any_is_untyped(self):
        from typing import Any
        assert target_python.from_native(Any) is None
        assert target_python.from_native("Any") is None
