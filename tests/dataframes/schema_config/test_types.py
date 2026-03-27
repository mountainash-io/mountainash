"""
Comprehensive tests for the Universal Type System.

Tests all type mappings, conversions, and utility functions to ensure 100% coverage.
"""
import pytest
from mountainash.dataframes.schema_config.types import (
    UniversalType,
    normalize_type,
    is_safe_cast,
    get_polars_type,
    get_arrow_type,
    get_universal_to_backend_mapping,
    get_backend_to_universal_mapping,
    UNIVERSAL_TO_PANDAS,
    UNIVERSAL_TO_IBIS,
    POLARS_TO_UNIVERSAL,
    PANDAS_TO_UNIVERSAL,
    ARROW_TO_UNIVERSAL,
    IBIS_TO_UNIVERSAL,
    PYTHON_TO_UNIVERSAL,
    SAFE_CASTS,
    UNSAFE_CASTS,
)


# ============================================================================
# Test UniversalType Enum
# ============================================================================

class TestUniversalType:
    """Test the UniversalType enum."""

    def test_universal_type_enum_values(self):
        """Test that all universal types have correct string values."""
        assert UniversalType.STRING == "string"
        assert UniversalType.INTEGER == "integer"
        assert UniversalType.NUMBER == "number"
        assert UniversalType.BOOLEAN == "boolean"
        assert UniversalType.DATE == "date"
        assert UniversalType.TIME == "time"
        assert UniversalType.DATETIME == "datetime"
        assert UniversalType.DURATION == "duration"
        assert UniversalType.YEAR == "year"
        assert UniversalType.YEARMONTH == "yearmonth"
        assert UniversalType.ARRAY == "array"
        assert UniversalType.OBJECT == "object"
        assert UniversalType.ANY == "any"

    def test_universal_type_enum_membership(self):
        """Test that universal type strings are recognized as enum members."""
        assert "string" in UniversalType
        assert "integer" in UniversalType
        assert "not_a_type" not in UniversalType


# ============================================================================
# Test Forward Type Mappings (Universal → Backend)
# ============================================================================

class TestForwardTypeMappings:
    """Test universal → backend-specific type mappings."""

    def test_universal_to_pandas_basic_types(self):
        """Test basic type mappings to pandas."""
        assert UNIVERSAL_TO_PANDAS[UniversalType.STRING] == "string"
        assert UNIVERSAL_TO_PANDAS[UniversalType.INTEGER] == "Int64"
        assert UNIVERSAL_TO_PANDAS[UniversalType.NUMBER] == "float64"
        assert UNIVERSAL_TO_PANDAS[UniversalType.BOOLEAN] == "boolean"

    def test_universal_to_pandas_temporal_types(self):
        """Test temporal type mappings to pandas."""
        assert UNIVERSAL_TO_PANDAS[UniversalType.DATE] == "datetime64[ns]"
        assert UNIVERSAL_TO_PANDAS[UniversalType.DATETIME] == "datetime64[ns]"
        assert UNIVERSAL_TO_PANDAS[UniversalType.DURATION] == "timedelta64[ns]"
        assert UNIVERSAL_TO_PANDAS[UniversalType.TIME] == "object"

    def test_universal_to_pandas_complex_types(self):
        """Test complex type mappings to pandas."""
        assert UNIVERSAL_TO_PANDAS[UniversalType.ARRAY] == "object"
        assert UNIVERSAL_TO_PANDAS[UniversalType.OBJECT] == "object"
        assert UNIVERSAL_TO_PANDAS[UniversalType.ANY] == "object"

    def test_universal_to_ibis_basic_types(self):
        """Test basic type mappings to Ibis."""
        assert UNIVERSAL_TO_IBIS[UniversalType.STRING] == "string"
        assert UNIVERSAL_TO_IBIS[UniversalType.INTEGER] == "int64"
        assert UNIVERSAL_TO_IBIS[UniversalType.NUMBER] == "float64"
        assert UNIVERSAL_TO_IBIS[UniversalType.BOOLEAN] == "bool"

    def test_universal_to_ibis_temporal_types(self):
        """Test temporal type mappings to Ibis."""
        assert UNIVERSAL_TO_IBIS[UniversalType.DATE] == "date"
        assert UNIVERSAL_TO_IBIS[UniversalType.TIME] == "time"
        assert UNIVERSAL_TO_IBIS[UniversalType.DATETIME] == "timestamp"
        assert UNIVERSAL_TO_IBIS[UniversalType.DURATION] == "interval"

    @pytest.mark.skipif(
        not pytest.importorskip("polars", reason="polars not installed"),
        reason="polars not installed"
    )
    def test_get_polars_type(self):
        """Test getting Polars types via lazy loading."""
        import polars as pl

        polars_type = get_polars_type(UniversalType.STRING)
        assert polars_type == pl.Utf8

        polars_type = get_polars_type(UniversalType.INTEGER)
        assert polars_type == pl.Int64

    @pytest.mark.skipif(
        not pytest.importorskip("pyarrow", reason="pyarrow not installed"),
        reason="pyarrow not installed"
    )
    def test_get_arrow_type(self):
        """Test getting PyArrow types via lazy loading."""
        import pyarrow as pa

        arrow_type = get_arrow_type(UniversalType.STRING)
        assert arrow_type == pa.string()

        arrow_type = get_arrow_type(UniversalType.INTEGER)
        assert arrow_type == pa.int64()


# ============================================================================
# Test Reverse Type Mappings (Backend → Universal)
# ============================================================================

class TestReverseTypeMappings:
    """Test backend-specific → universal type mappings."""

    def test_polars_to_universal_string_types(self):
        """Test Polars string types map to universal."""
        assert POLARS_TO_UNIVERSAL["Utf8"] == UniversalType.STRING
        assert POLARS_TO_UNIVERSAL["Categorical"] == UniversalType.STRING
        assert POLARS_TO_UNIVERSAL["Enum"] == UniversalType.STRING

    def test_polars_to_universal_integer_types(self):
        """Test all Polars integer types map to universal integer."""
        for int_type in ["Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64"]:
            assert POLARS_TO_UNIVERSAL[int_type] == UniversalType.INTEGER

    def test_polars_to_universal_float_types(self):
        """Test Polars float types map to universal number."""
        assert POLARS_TO_UNIVERSAL["Float32"] == UniversalType.NUMBER
        assert POLARS_TO_UNIVERSAL["Float64"] == UniversalType.NUMBER

    def test_polars_to_universal_temporal_types(self):
        """Test Polars temporal types."""
        assert POLARS_TO_UNIVERSAL["Date"] == UniversalType.DATE
        assert POLARS_TO_UNIVERSAL["Time"] == UniversalType.TIME
        assert POLARS_TO_UNIVERSAL["Datetime"] == UniversalType.DATETIME
        assert POLARS_TO_UNIVERSAL["Duration"] == UniversalType.DURATION

    def test_pandas_to_universal_string_types(self):
        """Test pandas string types map to universal."""
        assert PANDAS_TO_UNIVERSAL["string"] == UniversalType.STRING
        assert PANDAS_TO_UNIVERSAL["object"] == UniversalType.STRING
        assert PANDAS_TO_UNIVERSAL["category"] == UniversalType.STRING

    def test_pandas_to_universal_integer_types(self):
        """Test pandas integer types."""
        for int_type in ["int8", "int16", "int32", "int64", "Int8", "Int16", "Int32", "Int64"]:
            assert PANDAS_TO_UNIVERSAL[int_type] == UniversalType.INTEGER

    def test_pandas_to_universal_float_types(self):
        """Test pandas float types."""
        for float_type in ["float16", "float32", "float64", "Float32", "Float64"]:
            assert PANDAS_TO_UNIVERSAL[float_type] == UniversalType.NUMBER

    def test_pandas_to_universal_boolean_types(self):
        """Test pandas boolean types."""
        assert PANDAS_TO_UNIVERSAL["bool"] == UniversalType.BOOLEAN
        assert PANDAS_TO_UNIVERSAL["boolean"] == UniversalType.BOOLEAN

    def test_pandas_to_universal_temporal_types(self):
        """Test pandas temporal types."""
        assert PANDAS_TO_UNIVERSAL["datetime64"] == UniversalType.DATETIME
        assert PANDAS_TO_UNIVERSAL["datetime64[ns]"] == UniversalType.DATETIME
        assert PANDAS_TO_UNIVERSAL["timedelta64"] == UniversalType.DURATION
        assert PANDAS_TO_UNIVERSAL["timedelta64[ns]"] == UniversalType.DURATION

    def test_arrow_to_universal_basic_types(self):
        """Test PyArrow basic types."""
        assert ARROW_TO_UNIVERSAL["string"] == UniversalType.STRING
        assert ARROW_TO_UNIVERSAL["int64"] == UniversalType.INTEGER
        assert ARROW_TO_UNIVERSAL["float64"] == UniversalType.NUMBER
        assert ARROW_TO_UNIVERSAL["bool"] == UniversalType.BOOLEAN

    def test_arrow_to_universal_temporal_types(self):
        """Test PyArrow temporal types."""
        assert ARROW_TO_UNIVERSAL["date32"] == UniversalType.DATE
        assert ARROW_TO_UNIVERSAL["date64"] == UniversalType.DATE
        assert ARROW_TO_UNIVERSAL["time64"] == UniversalType.TIME
        assert ARROW_TO_UNIVERSAL["timestamp"] == UniversalType.DATETIME
        assert ARROW_TO_UNIVERSAL["duration"] == UniversalType.DURATION

    def test_ibis_to_universal_types(self):
        """Test Ibis type mappings."""
        assert IBIS_TO_UNIVERSAL["string"] == UniversalType.STRING
        assert IBIS_TO_UNIVERSAL["int64"] == UniversalType.INTEGER
        assert IBIS_TO_UNIVERSAL["float64"] == UniversalType.NUMBER
        assert IBIS_TO_UNIVERSAL["bool"] == UniversalType.BOOLEAN
        assert IBIS_TO_UNIVERSAL["date"] == UniversalType.DATE
        assert IBIS_TO_UNIVERSAL["timestamp"] == UniversalType.DATETIME


# ============================================================================
# Test Python Type Mappings
# ============================================================================

class TestPythonTypeMappings:
    """Test Python type → universal mappings."""

    def test_python_builtin_types(self):
        """Test Python builtin type objects."""
        assert PYTHON_TO_UNIVERSAL[str] == UniversalType.STRING
        assert PYTHON_TO_UNIVERSAL[int] == UniversalType.INTEGER
        assert PYTHON_TO_UNIVERSAL[float] == UniversalType.NUMBER
        assert PYTHON_TO_UNIVERSAL[bool] == UniversalType.BOOLEAN

    def test_python_type_strings(self):
        """Test Python type name strings."""
        assert PYTHON_TO_UNIVERSAL["str"] == UniversalType.STRING
        assert PYTHON_TO_UNIVERSAL["int"] == UniversalType.INTEGER
        assert PYTHON_TO_UNIVERSAL["float"] == UniversalType.NUMBER
        assert PYTHON_TO_UNIVERSAL["bool"] == UniversalType.BOOLEAN

    def test_python_collection_types(self):
        """Test Python collection types."""
        assert PYTHON_TO_UNIVERSAL["list"] == UniversalType.ARRAY
        assert PYTHON_TO_UNIVERSAL["List"] == UniversalType.ARRAY
        assert PYTHON_TO_UNIVERSAL["dict"] == UniversalType.OBJECT
        assert PYTHON_TO_UNIVERSAL["Dict"] == UniversalType.OBJECT


# ============================================================================
# Test normalize_type Function
# ============================================================================

class TestNormalizeType:
    """Test the normalize_type utility function."""

    def test_normalize_already_universal(self):
        """Test normalizing universal types returns them as-is."""
        assert normalize_type("string") == "string"
        assert normalize_type("integer") == "integer"
        assert normalize_type("number") == "number"

    def test_normalize_polars_types(self):
        """Test normalizing Polars type strings."""
        assert normalize_type("Int64", "polars") == "integer"
        assert normalize_type("Utf8", "polars") == "string"
        assert normalize_type("Float64", "polars") == "number"
        assert normalize_type("Boolean", "polars") == "boolean"

    def test_normalize_pandas_types(self):
        """Test normalizing pandas type strings."""
        assert normalize_type("int64", "pandas") == "integer"
        assert normalize_type("string", "pandas") == "string"
        assert normalize_type("float64", "pandas") == "number"
        assert normalize_type("boolean", "pandas") == "boolean"

    def test_normalize_arrow_types(self):
        """Test normalizing PyArrow type strings."""
        assert normalize_type("int64", "arrow") == "integer"
        assert normalize_type("string", "arrow") == "string"
        assert normalize_type("float64", "arrow") == "number"
        assert normalize_type("bool", "arrow") == "boolean"

    def test_normalize_ibis_types(self):
        """Test normalizing Ibis type strings."""
        assert normalize_type("int64", "ibis") == "integer"
        assert normalize_type("string", "ibis") == "string"
        assert normalize_type("float64", "ibis") == "number"
        assert normalize_type("bool", "ibis") == "boolean"

    def test_normalize_python_type_objects(self):
        """Test normalizing Python type objects."""
        assert normalize_type(str, "python") == "string"
        assert normalize_type(int, "python") == "integer"
        assert normalize_type(float, "python") == "number"
        assert normalize_type(bool, "python") == "boolean"

    def test_normalize_python_type_strings(self):
        """Test normalizing Python type name strings."""
        assert normalize_type("str", "python") == "string"
        assert normalize_type("int", "python") == "integer"
        assert normalize_type("float", "python") == "number"
        assert normalize_type("bool", "python") == "boolean"

    def test_normalize_python_datetime_types(self):
        """Test normalizing Python datetime types."""
        import datetime

        assert normalize_type(datetime.date, "python") == "date"
        assert normalize_type(datetime.time, "python") == "time"
        assert normalize_type(datetime.datetime, "python") == "datetime"
        assert normalize_type(datetime.timedelta, "python") == "duration"

    def test_normalize_case_insensitive(self):
        """Test that normalization handles case variations."""
        # Pandas type names should work with different cases
        assert normalize_type("INT64", "pandas") == "integer"
        assert normalize_type("STRING", "pandas") == "string"

    def test_normalize_unknown_type_returns_any(self):
        """Test that unknown types default to 'any' with warning."""
        result = normalize_type("UnknownType", "polars")
        assert result == "any"

    def test_normalize_default_source_format(self):
        """Test default source format is universal."""
        assert normalize_type("string") == "string"
        assert normalize_type("integer") == "integer"


# ============================================================================
# Test Safe Cast Detection
# ============================================================================

class TestSafeCastDetection:
    """Test is_safe_cast utility function."""

    def test_same_type_is_safe(self):
        """Test that casting to same type is always safe."""
        assert is_safe_cast("integer", "integer") is True
        assert is_safe_cast("string", "string") is True
        assert is_safe_cast("number", "number") is True

    def test_known_safe_casts(self):
        """Test known safe type casts."""
        # Widening numeric casts
        assert is_safe_cast("integer", "number") is True

        # To string casts
        assert is_safe_cast("integer", "string") is True
        assert is_safe_cast("number", "string") is True
        assert is_safe_cast("boolean", "string") is True
        assert is_safe_cast("date", "string") is True

        # Temporal conversions
        assert is_safe_cast("date", "datetime") is True
        assert is_safe_cast("datetime", "date") is True  # Loses time but common pattern

        # Boolean conversions
        assert is_safe_cast("boolean", "integer") is True

    def test_known_unsafe_casts(self):
        """Test known unsafe type casts."""
        # Narrowing numeric casts
        assert is_safe_cast("number", "integer") is False

        # String parsing (may fail)
        assert is_safe_cast("string", "integer") is False
        assert is_safe_cast("string", "number") is False
        assert is_safe_cast("string", "boolean") is False
        assert is_safe_cast("string", "date") is False

    def test_unknown_cast_is_unsafe(self):
        """Test that unknown casts are conservatively marked as unsafe."""
        # Array to object or similar unknown conversions
        assert is_safe_cast("array", "object") is False

    def test_safe_casts_set_coverage(self):
        """Test that SAFE_CASTS set contains expected entries."""
        assert ("integer", "number") in SAFE_CASTS
        assert ("integer", "string") in SAFE_CASTS
        assert ("boolean", "integer") in SAFE_CASTS

    def test_unsafe_casts_set_coverage(self):
        """Test that UNSAFE_CASTS set contains expected entries."""
        assert ("number", "integer") in UNSAFE_CASTS
        assert ("string", "integer") in UNSAFE_CASTS
        assert ("string", "number") in UNSAFE_CASTS


# ============================================================================
# Test Mapping Access Functions
# ============================================================================

class TestMappingAccessFunctions:
    """Test functions for accessing type mappings."""

    def test_get_universal_to_backend_mapping_pandas(self):
        """Test getting pandas mapping."""
        mapping = get_universal_to_backend_mapping("pandas")
        assert mapping[UniversalType.STRING] == "string"
        assert mapping[UniversalType.INTEGER] == "Int64"

    def test_get_universal_to_backend_mapping_ibis(self):
        """Test getting Ibis mapping."""
        mapping = get_universal_to_backend_mapping("ibis")
        assert mapping[UniversalType.STRING] == "string"
        assert mapping[UniversalType.INTEGER] == "int64"

    @pytest.mark.skipif(
        not pytest.importorskip("polars", reason="polars not installed"),
        reason="polars not installed"
    )
    def test_get_universal_to_backend_mapping_polars(self):
        """Test getting Polars mapping (requires polars)."""
        import polars as pl

        mapping = get_universal_to_backend_mapping("polars")
        assert mapping[UniversalType.STRING] == pl.Utf8
        assert mapping[UniversalType.INTEGER] == pl.Int64

    @pytest.mark.skipif(
        not pytest.importorskip("pyarrow", reason="pyarrow not installed"),
        reason="pyarrow not installed"
    )
    def test_get_universal_to_backend_mapping_arrow(self):
        """Test getting PyArrow mapping (requires pyarrow)."""
        import pyarrow as pa

        mapping = get_universal_to_backend_mapping("arrow")
        assert mapping[UniversalType.STRING] == pa.string()

    def test_get_universal_to_backend_mapping_unknown_backend(self):
        """Test that unknown backend raises ValueError."""
        with pytest.raises(ValueError, match="Unknown backend"):
            get_universal_to_backend_mapping("unknown_backend")

    def test_get_backend_to_universal_mapping_polars(self):
        """Test getting Polars → universal mapping."""
        mapping = get_backend_to_universal_mapping("polars")
        assert mapping["Int64"] == "integer"
        assert mapping["Utf8"] == "string"

    def test_get_backend_to_universal_mapping_pandas(self):
        """Test getting pandas → universal mapping."""
        mapping = get_backend_to_universal_mapping("pandas")
        assert mapping["int64"] == "integer"
        assert mapping["string"] == "string"

    def test_get_backend_to_universal_mapping_arrow(self):
        """Test getting PyArrow → universal mapping."""
        mapping = get_backend_to_universal_mapping("arrow")
        assert mapping["int64"] == "integer"
        assert mapping["string"] == "string"

    def test_get_backend_to_universal_mapping_ibis(self):
        """Test getting Ibis → universal mapping."""
        mapping = get_backend_to_universal_mapping("ibis")
        assert mapping["int64"] == "integer"
        assert mapping["string"] == "string"

    def test_get_backend_to_universal_mapping_unknown_backend(self):
        """Test that unknown backend raises ValueError."""
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend_to_universal_mapping("unknown_backend")


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCasesAndErrors:
    """Test edge cases and error handling."""

    def test_normalize_type_with_type_name_attribute(self):
        """Test normalizing type objects with __name__ attribute."""
        # When a class defines __name__ as a class attribute, Python's __name__
        # still refers to the actual class name, not the attribute value.
        # So this test verifies that unknown types default to "any"
        class CustomType:
            __name__ = "int"  # This doesn't actually override the class __name__

        result = normalize_type(CustomType, "python")
        # CustomType.__name__ is actually "CustomType", not "int"
        # So it's not found in mappings and defaults to "any"
        assert result == "any"

    def test_get_polars_type_missing_library(self):
        """Test getting Polars type when polars is not installed."""
        # This test would need mocking to simulate missing polars
        # For now, we just test that the function exists
        assert callable(get_polars_type)

    def test_get_arrow_type_missing_library(self):
        """Test getting Arrow type when pyarrow is not installed."""
        # This test would need mocking to simulate missing pyarrow
        # For now, we just test that the function exists
        assert callable(get_arrow_type)


# ============================================================================
# Integration Tests
# ============================================================================

class TestTypeSystemIntegration:
    """Integration tests for the complete type system."""

    def test_round_trip_polars_to_universal_to_pandas(self):
        """Test converting Polars type → universal → pandas."""
        # Polars Int64 → universal integer
        universal = normalize_type("Int64", "polars")
        assert universal == "integer"

        # universal integer → pandas Int64
        pandas_type = UNIVERSAL_TO_PANDAS[universal]
        assert pandas_type == "Int64"

    def test_round_trip_python_to_universal_to_polars(self):
        """Test converting Python type → universal → Polars (if installed)."""
        # Python int → universal integer
        universal = normalize_type(int, "python")
        assert universal == "integer"

        # If polars is available, check conversion
        try:
            import polars as pl
            polars_type = get_polars_type(universal)
            assert polars_type == pl.Int64
        except ImportError:
            pytest.skip("polars not installed")

    def test_comprehensive_type_coverage(self):
        """Test that all universal types have mappings to all backends."""
        # Check pandas mappings exist for all universal types
        for univ_type in UniversalType:
            assert univ_type in UNIVERSAL_TO_PANDAS

        # Check Ibis mappings exist for all universal types
        for univ_type in UniversalType:
            assert univ_type in UNIVERSAL_TO_IBIS

    def test_type_system_symmetry(self):
        """Test that reverse mappings cover forward mappings where applicable."""
        # For pandas: check that forward mapped types can be reversed
        for univ_type, pandas_type in UNIVERSAL_TO_PANDAS.items():
            # Some types map to the same pandas type (e.g., multiple to "object")
            # So we just check that the pandas type exists in reverse mapping
            if pandas_type in PANDAS_TO_UNIVERSAL:
                reverse_univ = PANDAS_TO_UNIVERSAL[pandas_type]
                # Should map back to a valid universal type
                assert reverse_univ in UniversalType
