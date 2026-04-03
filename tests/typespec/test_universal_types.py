"""
Tests for the UniversalType enum and the type normalization/mapping system.

Coverage:
- UniversalType StrEnum membership and values
- normalize_type() across all source formats
- Forward mappings: Universal → Polars, Arrow, Pandas, Ibis
- Reverse mappings: Polars, Pandas, Arrow, Ibis → Universal
- Safe/unsafe cast detection
"""
from __future__ import annotations

import datetime

import pytest

from mountainash.typespec.universal_types import (
    ARROW_TO_UNIVERSAL,
    IBIS_TO_UNIVERSAL,
    PANDAS_TO_UNIVERSAL,
    POLARS_TO_UNIVERSAL,
    PYTHON_TO_UNIVERSAL,
    SAFE_CASTS,
    UNSAFE_CASTS,
    UNIVERSAL_TO_IBIS,
    UNIVERSAL_TO_PANDAS,
    UniversalType,
    get_arrow_type,
    get_backend_to_universal_mapping,
    get_polars_type,
    get_universal_to_backend_mapping,
    is_safe_cast,
    normalize_type,
)


# ============================================================================
# TestUniversalTypeEnum
# ============================================================================

_ALL_MEMBERS = [
    ("STRING", "string"),
    ("INTEGER", "integer"),
    ("NUMBER", "number"),
    ("BOOLEAN", "boolean"),
    ("DATE", "date"),
    ("TIME", "time"),
    ("DATETIME", "datetime"),
    ("DURATION", "duration"),
    ("YEAR", "year"),
    ("YEARMONTH", "yearmonth"),
    ("ARRAY", "array"),
    ("OBJECT", "object"),
    ("ANY", "any"),
]


class TestUniversalTypeEnum:
    """UniversalType is a StrEnum with 13 members, each value == lowercase name."""

    def test_member_count(self):
        assert len(UniversalType) == 13

    @pytest.mark.parametrize("name,value", _ALL_MEMBERS)
    def test_member_exists(self, name, value):
        assert hasattr(UniversalType, name)

    @pytest.mark.parametrize("name,value", _ALL_MEMBERS)
    def test_member_value(self, name, value):
        assert getattr(UniversalType, name).value == value

    @pytest.mark.parametrize("name,value", _ALL_MEMBERS)
    def test_strenum_equality(self, name, value):
        """StrEnum members should compare equal to their string value."""
        member = getattr(UniversalType, name)
        assert member == value

    def test_is_strenum(self):
        from enum import StrEnum
        assert issubclass(UniversalType, StrEnum)

    def test_string_comparison(self):
        assert UniversalType.STRING == "string"
        assert UniversalType.INTEGER == "integer"


# ============================================================================
# TestNormalizeTypePython
# ============================================================================

class TestNormalizeTypePython:
    """normalize_type() with Python type objects."""

    @pytest.mark.parametrize("python_type,expected", [
        (int, "integer"),
        (float, "number"),
        (str, "string"),
        (bool, "boolean"),
        (datetime.date, "date"),
        (datetime.datetime, "datetime"),
        (datetime.time, "time"),
        (datetime.timedelta, "duration"),
    ])
    def test_python_type_objects(self, python_type, expected):
        result = normalize_type(python_type, "python")
        assert result == expected


# ============================================================================
# TestNormalizeTypeIdentity
# ============================================================================

class TestNormalizeTypeIdentity:
    """Universal type strings passed to normalize_type() return themselves."""

    @pytest.mark.parametrize("type_str", [
        "string", "integer", "number", "boolean",
        "date", "time", "datetime", "duration",
        "year", "yearmonth", "array", "object", "any",
    ])
    def test_identity(self, type_str):
        result = normalize_type(type_str, "universal")
        assert result == type_str

    @pytest.mark.parametrize("type_str", [
        "string", "integer", "number", "boolean",
        "date", "time", "datetime", "duration",
    ])
    def test_identity_default_format(self, type_str):
        """Default source_format is 'universal', so identity should work without specifying."""
        result = normalize_type(type_str)
        assert result == type_str


# ============================================================================
# TestNormalizeTypePolars
# ============================================================================

class TestNormalizeTypePolars:
    """normalize_type() with Polars-style string type names."""

    @pytest.mark.parametrize("polars_type,expected", [
        ("Utf8", "string"),
        ("String", "string"),
        ("Int64", "integer"),
        ("Int32", "integer"),
        ("Float64", "number"),
        ("Boolean", "boolean"),
        ("Date", "date"),
        ("Datetime", "datetime"),
        ("Duration", "duration"),
        ("Time", "time"),
        ("List", "array"),
        ("Struct", "object"),
    ])
    def test_polars_types(self, polars_type, expected):
        result = normalize_type(polars_type, "polars")
        assert result == expected


# ============================================================================
# TestNormalizeTypePandas
# ============================================================================

class TestNormalizeTypePandas:
    """normalize_type() with pandas-style dtype strings."""

    @pytest.mark.parametrize("pandas_type,expected", [
        # NOTE: "object" is also UniversalType.OBJECT, so normalize_type() short-circuits
        # to identity ("object") before reaching the pandas mapping.  Test the actual
        # behaviour rather than the conceptual pandas convention.
        ("object", "object"),
        ("string", "string"),
        ("int64", "integer"),
        ("Int64", "integer"),
        ("float64", "number"),
        ("bool", "boolean"),
        ("boolean", "boolean"),
        ("datetime64[ns]", "datetime"),
        ("timedelta64[ns]", "duration"),
    ])
    def test_pandas_types(self, pandas_type, expected):
        result = normalize_type(pandas_type, "pandas")
        assert result == expected


# ============================================================================
# TestNormalizeTypeArrow
# ============================================================================

class TestNormalizeTypeArrow:
    """normalize_type() with PyArrow type name strings."""

    @pytest.mark.parametrize("arrow_type,expected", [
        ("string", "string"),
        ("int64", "integer"),
        ("float64", "number"),
        ("bool", "boolean"),
        ("date32", "date"),
        ("timestamp", "datetime"),
        ("duration", "duration"),
        ("time64", "time"),
    ])
    def test_arrow_types(self, arrow_type, expected):
        result = normalize_type(arrow_type, "arrow")
        assert result == expected


# ============================================================================
# TestNormalizeTypeIbis
# ============================================================================

class TestNormalizeTypeIbis:
    """normalize_type() with Ibis type name strings."""

    @pytest.mark.parametrize("ibis_type,expected", [
        ("string", "string"),
        ("int64", "integer"),
        ("float64", "number"),
        ("bool", "boolean"),
        ("date", "date"),
        ("timestamp", "datetime"),
        ("interval", "duration"),
    ])
    def test_ibis_types(self, ibis_type, expected):
        result = normalize_type(ibis_type, "ibis")
        assert result == expected


# ============================================================================
# TestForwardMappings
# ============================================================================

class TestForwardMappings:
    """Forward mappings: UniversalType → backend-specific types."""

    def test_universal_to_polars_covers_all(self):
        mapping = get_universal_to_backend_mapping("polars")
        for ut in UniversalType:
            assert ut in mapping or ut.value in mapping, (
                f"No Polars mapping for UniversalType.{ut.name}"
            )

    def test_get_polars_type_integer(self):
        import polars as pl
        result = get_polars_type("integer")
        assert result is pl.Int64

    def test_get_polars_type_string(self):
        import polars as pl
        result = get_polars_type("string")
        assert result is pl.Utf8

    def test_get_arrow_type_integer(self):
        import pyarrow as pa
        result = get_arrow_type("integer")
        assert result == pa.int64()

    def test_get_arrow_type_string(self):
        import pyarrow as pa
        result = get_arrow_type("string")
        assert result == pa.string()

    def test_universal_to_pandas_covers_all(self):
        for ut in UniversalType:
            assert ut in UNIVERSAL_TO_PANDAS or ut.value in UNIVERSAL_TO_PANDAS, (
                f"No pandas mapping for UniversalType.{ut.name}"
            )

    def test_universal_to_ibis_covers_all(self):
        for ut in UniversalType:
            assert ut in UNIVERSAL_TO_IBIS or ut.value in UNIVERSAL_TO_IBIS, (
                f"No Ibis mapping for UniversalType.{ut.name}"
            )

    @pytest.mark.parametrize("backend", ["polars", "pandas", "arrow", "ibis"])
    def test_forward_mapping_has_all_universal_types(self, backend):
        mapping = get_universal_to_backend_mapping(backend)
        assert len(mapping) >= len(UniversalType)


# ============================================================================
# TestReverseMappings
# ============================================================================

class TestReverseMappings:
    """Reverse mappings: backend-specific types → UniversalType."""

    @pytest.mark.parametrize("backend", ["polars", "pandas", "arrow", "ibis"])
    def test_reverse_mapping_non_empty(self, backend):
        mapping = get_backend_to_universal_mapping(backend)
        assert len(mapping) > 0

    def test_polars_to_universal_common_keys(self):
        for key in ("Int64", "Float64", "Utf8", "Boolean", "Date"):
            assert key in POLARS_TO_UNIVERSAL, f"Missing key: {key}"

    def test_pandas_to_universal_common_keys(self):
        for key in ("int64", "float64", "object", "bool", "datetime64[ns]"):
            assert key in PANDAS_TO_UNIVERSAL, f"Missing key: {key}"

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError):
            get_backend_to_universal_mapping("nonexistent_backend")


# ============================================================================
# TestSafeCasts
# ============================================================================

class TestSafeCasts:
    """is_safe_cast() and the SAFE_CASTS / UNSAFE_CASTS sets."""

    @pytest.mark.parametrize("type_str", [
        "integer", "string", "number", "boolean", "date", "datetime",
    ])
    def test_same_type_is_safe(self, type_str):
        assert is_safe_cast(type_str, type_str) is True

    @pytest.mark.parametrize("from_t,to_t", list(SAFE_CASTS))
    def test_safe_cast_pairs(self, from_t, to_t):
        assert is_safe_cast(from_t, to_t) is True

    @pytest.mark.parametrize("from_t,to_t", list(UNSAFE_CASTS))
    def test_unsafe_cast_pairs(self, from_t, to_t):
        assert is_safe_cast(from_t, to_t) is False

    def test_safe_and_unsafe_disjoint(self):
        overlap = SAFE_CASTS & UNSAFE_CASTS
        assert overlap == set(), f"Overlapping entries: {overlap}"

    def test_unknown_pair_returns_false(self):
        """Unknown casts are conservative — assume unsafe."""
        assert is_safe_cast("year", "yearmonth") is False
        assert is_safe_cast("array", "object") is False
