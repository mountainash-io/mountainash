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

    def test_parse_type_string_parameterized_round_trips(self):
        # Parameterized reprs now reconstruct via the safe-eval parser
        # (item 54, gap 1) — no longer dropped to canonical fallback.
        assert target_polars.parse_type_string(
            "Datetime(time_unit='us', time_zone=None)"
        ) == pl.Datetime(time_unit="us", time_zone=None)

    def test_parse_type_string_garbage_returns_none(self):
        assert target_polars.parse_type_string("garbage") is None


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


# ============================================================================
# TestSemanticStringTargets (item 113 Unit B, Task 2)
#
# JSON, XSD_DURATION, XSD_YEAR, XSD_YEARMONTH map to each target's string
# physical type. None of the four enters CAST_UNSUPPORTED. Native reverse
# maps are UNCHANGED — a native string still infers only STRING, never one
# of the semantic subtypes (physically indistinguishable).
# ============================================================================

_SEMANTIC_STRING_DTYPES = (D.JSON, D.XSD_DURATION, D.XSD_YEAR, D.XSD_YEARMONTH)


class TestSemanticStringTargets:
    def test_polars_maps_to_string(self):
        for d in _SEMANTIC_STRING_DTYPES:
            assert target_polars.SCHEMA_TYPES[d] is pl.String

    def test_pyarrow_maps_to_string(self):
        import pyarrow as pa
        for d in _SEMANTIC_STRING_DTYPES:
            assert target_pyarrow.SCHEMA_TYPES[d] == pa.string()

    def test_pandas_maps_to_string(self):
        for d in _SEMANTIC_STRING_DTYPES:
            assert target_pandas.SCHEMA_TYPES[d] == "string"

    def test_ibis_maps_to_string(self):
        for d in _SEMANTIC_STRING_DTYPES:
            assert target_ibis.SCHEMA_TYPES[d] == "string"

    def test_narwhals_maps_to_string(self):
        import narwhals as nw
        for d in _SEMANTIC_STRING_DTYPES:
            assert target_narwhals.SCHEMA_TYPES[d] is nw.String

    def test_python_maps_to_str(self):
        for d in _SEMANTIC_STRING_DTYPES:
            assert target_python.SCHEMA_TYPES[d] is str

    @pytest.mark.parametrize("mod", [
        target_polars, target_pyarrow, target_pandas, target_ibis,
        target_narwhals, target_python,
    ])
    def test_none_are_cast_unsupported(self, mod):
        for d in _SEMANTIC_STRING_DTYPES:
            assert d not in mod.CAST_UNSUPPORTED

    def test_native_string_still_infers_only_string_polars(self):
        assert target_polars.from_native(pl.String) is D.STRING
        assert target_polars.from_native(pl.String()) is D.STRING

    def test_native_string_still_infers_only_string_pyarrow(self):
        import pyarrow as pa
        assert target_pyarrow.from_native(pa.string()) is D.STRING

    def test_native_string_still_infers_only_string_pandas(self):
        assert target_pandas.from_native("string") is D.STRING

    def test_native_string_still_infers_only_string_ibis(self):
        assert target_ibis.from_native("string") is D.STRING

    def test_native_string_still_infers_only_string_narwhals(self):
        import narwhals as nw
        assert target_narwhals.from_native(nw.String) is D.STRING

    def test_native_string_still_infers_only_string_python(self):
        assert target_python.from_native(str) is D.STRING
        assert target_python.from_native("str") is D.STRING
