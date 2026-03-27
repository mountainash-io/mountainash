"""
Unit tests for custom type conversion system.

Tests the CustomTypeRegistry, TypeConverter protocol, TypeConverterSpec,
and standard converters (safe_float, safe_int, xml_string, rich_boolean).
"""
import pytest
import math
from mountainash.dataframes.schema_config import (
    CustomTypeRegistry,
    TypeConverterSpec,
    SchemaConfig,
)
from mountainash.dataframes.schema_config.types import UniversalType


class TestTypeConverterSpec:
    """Test TypeConverterSpec dataclass."""

    def test_create_spec(self):
        """Test creating a TypeConverterSpec."""
        def my_converter(value, *, field_name=None):
            return str(value)

        spec = TypeConverterSpec(
            name="my_converter",
            converter=my_converter,
            target_universal_type=UniversalType.STRING,
            description="Test converter",
            direction="both"
        )

        assert spec.name == "my_converter"
        assert spec.converter == my_converter
        assert spec.target_universal_type == UniversalType.STRING
        assert spec.description == "Test converter"
        assert spec.direction == "both"

    def test_invalid_direction(self):
        """Test that invalid direction raises ValueError."""
        def my_converter(value, *, field_name=None):
            return str(value)

        with pytest.raises(ValueError, match="Invalid direction"):
            TypeConverterSpec(
                name="my_converter",
                converter=my_converter,
                target_universal_type=UniversalType.STRING,
                direction="invalid"
            )


class TestCustomTypeRegistry:
    """Test CustomTypeRegistry class."""

    def setup_method(self):
        """Clear registry before each test."""
        # Note: Standard converters are auto-registered, so we don't clear them
        pass

    def test_standard_converters_registered(self):
        """Test that standard converters are registered on import."""
        assert CustomTypeRegistry.has_converter("safe_float")
        assert CustomTypeRegistry.has_converter("safe_int")
        assert CustomTypeRegistry.has_converter("xml_string")
        assert CustomTypeRegistry.has_converter("rich_boolean")

    def test_register_converter(self):
        """Test registering a custom converter."""
        def my_converter(value, *, field_name=None):
            return str(value).upper()

        CustomTypeRegistry.register(
            name="uppercase",
            converter=my_converter,
            target_universal_type=UniversalType.STRING,
            description="Convert to uppercase"
        )

        assert CustomTypeRegistry.has_converter("uppercase")
        spec = CustomTypeRegistry.get_spec("uppercase")
        assert spec.name == "uppercase"
        assert spec.target_universal_type == UniversalType.STRING
        assert spec.description == "Convert to uppercase"

        # Clean up
        CustomTypeRegistry.unregister("uppercase")

    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate name raises ValueError."""
        def my_converter(value, *, field_name=None):
            return value

        CustomTypeRegistry.register(
            name="test_duplicate",
            converter=my_converter,
            target_universal_type=UniversalType.STRING
        )

        with pytest.raises(ValueError, match="already registered"):
            CustomTypeRegistry.register(
                name="test_duplicate",
                converter=my_converter,
                target_universal_type=UniversalType.STRING
            )

        # Clean up
        CustomTypeRegistry.unregister("test_duplicate")

    def test_unregister_converter(self):
        """Test unregistering a converter."""
        def my_converter(value, *, field_name=None):
            return value

        CustomTypeRegistry.register(
            name="test_unregister",
            converter=my_converter,
            target_universal_type=UniversalType.STRING
        )

        assert CustomTypeRegistry.has_converter("test_unregister")

        result = CustomTypeRegistry.unregister("test_unregister")
        assert result is True
        assert not CustomTypeRegistry.has_converter("test_unregister")

    def test_unregister_nonexistent(self):
        """Test unregistering a nonexistent converter returns False."""
        result = CustomTypeRegistry.unregister("nonexistent")
        assert result is False

    def test_has_converter(self):
        """Test checking if converter exists."""
        assert CustomTypeRegistry.has_converter("safe_float")
        assert not CustomTypeRegistry.has_converter("nonexistent")

    def test_get_spec(self):
        """Test getting converter spec."""
        spec = CustomTypeRegistry.get_spec("safe_float")
        assert spec is not None
        assert spec.name == "safe_float"
        assert spec.target_universal_type == UniversalType.NUMBER

        spec = CustomTypeRegistry.get_spec("nonexistent")
        assert spec is None

    def test_convert_with_registered_converter(self):
        """Test converting a value with a registered converter."""
        result = CustomTypeRegistry.convert(42.5, "safe_float")
        assert result == 42.5

        result = CustomTypeRegistry.convert(None, "safe_float")
        assert result is None

    def test_convert_with_nonexistent_converter_raises_error(self):
        """Test converting with nonexistent converter raises ValueError."""
        with pytest.raises(ValueError, match="No converter registered"):
            CustomTypeRegistry.convert(42, "nonexistent")

    def test_convert_with_nonexistent_converter_no_raise(self):
        """Test converting with nonexistent converter returns value unchanged when raise_on_error=False."""
        result = CustomTypeRegistry.convert(42, "nonexistent", raise_on_error=False)
        assert result == 42

    def test_convert_with_field_name(self):
        """Test converting with field_name for error messages."""
        # This should work fine
        result = CustomTypeRegistry.convert("yes", "rich_boolean", field_name="is_active")
        assert result is True

        # This should fail with field name in error
        with pytest.raises(ValueError, match="field 'is_active'"):
            CustomTypeRegistry.convert("invalid", "rich_boolean", field_name="is_active")

    def test_is_native_type(self):
        """Test is_native_type method (KEY for hybrid strategy)."""
        # Native types (from UniversalType)
        assert CustomTypeRegistry.is_native_type("integer") is True
        assert CustomTypeRegistry.is_native_type("number") is True
        assert CustomTypeRegistry.is_native_type("string") is True
        assert CustomTypeRegistry.is_native_type("boolean") is True

        # Custom types (registered converters)
        assert CustomTypeRegistry.is_native_type("safe_float") is False
        assert CustomTypeRegistry.is_native_type("safe_int") is False
        assert CustomTypeRegistry.is_native_type("xml_string") is False
        assert CustomTypeRegistry.is_native_type("rich_boolean") is False

        # Unknown types (assume native)
        assert CustomTypeRegistry.is_native_type("unknown_type") is True

    def test_list_converters(self):
        """Test listing all registered converters."""
        converters = CustomTypeRegistry.list_converters()

        assert "safe_float" in converters
        assert "safe_int" in converters
        assert "xml_string" in converters
        assert "rich_boolean" in converters

        assert isinstance(converters["safe_float"], str)
        assert len(converters["safe_float"]) > 0


class TestStandardConverters:
    """Test standard converters (safe_float, safe_int, xml_string, rich_boolean)."""

    def test_safe_float_with_valid_values(self):
        """Test safe_float converter with valid values."""
        assert CustomTypeRegistry.convert(42.5, "safe_float") == 42.5
        assert CustomTypeRegistry.convert(42, "safe_float") == 42.0
        assert CustomTypeRegistry.convert("42.5", "safe_float") == 42.5
        assert CustomTypeRegistry.convert(None, "safe_float") is None

    def test_safe_float_with_nan(self):
        """Test safe_float converter with NaN."""
        result = CustomTypeRegistry.convert(float('nan'), "safe_float")
        assert result is None

    def test_safe_float_with_invalid_value(self):
        """Test safe_float converter with invalid value."""
        with pytest.raises(ValueError):
            CustomTypeRegistry.convert("invalid", "safe_float")

    def test_safe_int_with_valid_values(self):
        """Test safe_int converter with valid values."""
        assert CustomTypeRegistry.convert(42, "safe_int") == 42
        assert CustomTypeRegistry.convert(42.7, "safe_int") == 42  # Truncates
        assert CustomTypeRegistry.convert("42", "safe_int") == 42
        assert CustomTypeRegistry.convert(None, "safe_int") is None

    def test_safe_int_with_nan(self):
        """Test safe_int converter with NaN."""
        result = CustomTypeRegistry.convert(float('nan'), "safe_int")
        assert result is None

    def test_safe_int_with_invalid_value(self):
        """Test safe_int converter with invalid value."""
        with pytest.raises(ValueError):
            CustomTypeRegistry.convert("invalid", "safe_int")

    def test_xml_string_with_valid_values(self):
        """Test xml_string converter with valid values."""
        assert CustomTypeRegistry.convert("hello", "xml_string") == "hello"
        assert CustomTypeRegistry.convert(None, "xml_string") is None

    def test_xml_string_with_special_characters(self):
        """Test xml_string converter with XML special characters."""
        assert CustomTypeRegistry.convert("a&b", "xml_string") == "a&amp;b"
        assert CustomTypeRegistry.convert("a<b", "xml_string") == "a&lt;b"
        assert CustomTypeRegistry.convert("a>b", "xml_string") == "a&gt;b"
        assert CustomTypeRegistry.convert('a"b', "xml_string") == "a&quot;b"
        assert CustomTypeRegistry.convert("a'b", "xml_string") == "a&apos;b"
        assert CustomTypeRegistry.convert("<tag>value</tag>", "xml_string") == "&lt;tag&gt;value&lt;/tag&gt;"

    def test_rich_boolean_with_boolean_values(self):
        """Test rich_boolean converter with boolean values."""
        assert CustomTypeRegistry.convert(True, "rich_boolean") is True
        assert CustomTypeRegistry.convert(False, "rich_boolean") is False
        assert CustomTypeRegistry.convert(None, "rich_boolean") is None

    def test_rich_boolean_with_numeric_values(self):
        """Test rich_boolean converter with numeric values."""
        assert CustomTypeRegistry.convert(1, "rich_boolean") is True
        assert CustomTypeRegistry.convert(0, "rich_boolean") is False
        assert CustomTypeRegistry.convert(1.0, "rich_boolean") is True
        assert CustomTypeRegistry.convert(0.0, "rich_boolean") is False

    def test_rich_boolean_with_string_values(self):
        """Test rich_boolean converter with string values."""
        # Yes/No
        assert CustomTypeRegistry.convert("yes", "rich_boolean") is True
        assert CustomTypeRegistry.convert("no", "rich_boolean") is False
        assert CustomTypeRegistry.convert("YES", "rich_boolean") is True
        assert CustomTypeRegistry.convert("NO", "rich_boolean") is False

        # True/False
        assert CustomTypeRegistry.convert("true", "rich_boolean") is True
        assert CustomTypeRegistry.convert("false", "rich_boolean") is False
        assert CustomTypeRegistry.convert("TRUE", "rich_boolean") is True
        assert CustomTypeRegistry.convert("FALSE", "rich_boolean") is False

        # 1/0
        assert CustomTypeRegistry.convert("1", "rich_boolean") is True
        assert CustomTypeRegistry.convert("0", "rich_boolean") is False

    def test_rich_boolean_with_invalid_numeric(self):
        """Test rich_boolean converter with invalid numeric values."""
        with pytest.raises(ValueError, match="expected 0 or 1"):
            CustomTypeRegistry.convert(2, "rich_boolean")

        with pytest.raises(ValueError, match="expected 0 or 1"):
            CustomTypeRegistry.convert(-1, "rich_boolean")

    def test_rich_boolean_with_invalid_string(self):
        """Test rich_boolean converter with invalid string values."""
        with pytest.raises(ValueError, match="expected yes/no"):
            CustomTypeRegistry.convert("invalid", "rich_boolean")

        with pytest.raises(ValueError, match="expected yes/no"):
            CustomTypeRegistry.convert("maybe", "rich_boolean")


class TestSchemaConfigSeparateConversions:
    """Test SchemaConfig.separate_conversions() method (KEY for hybrid strategy)."""

    def test_separate_conversions_with_custom_and_native(self):
        """Test separating custom and native conversions."""
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native
            "amount": {"cast": "safe_float"},    # Narwhals custom (vectorized)
            "name": {"rename": "full_name"},     # Native (no cast)
            "active": {"cast": "rich_boolean"}   # Narwhals custom (vectorized)
        })

        python_only, narwhals, native = config.separate_conversions()

        # Check Narwhals custom conversions (safe_float and rich_boolean are vectorized)
        assert "amount" in narwhals
        assert narwhals["amount"]["cast"] == "safe_float"
        assert "active" in narwhals
        assert narwhals["active"]["cast"] == "rich_boolean"

        # Check no Python-only custom (all custom types now have Narwhals implementations)
        assert len(python_only) == 0

        # Check native conversions
        assert "id" in native
        assert native["id"]["cast"] == "integer"
        assert "name" in native
        assert native["name"]["rename"] == "full_name"

    def test_separate_conversions_with_only_native(self):
        """Test separating when only native conversions present."""
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "score": {"cast": "number"},
            "name": {"rename": "full_name"}
        })

        python_only, narwhals, native = config.separate_conversions()

        assert len(python_only) == 0
        assert len(narwhals) == 0
        assert len(native) == 3
        assert "id" in native
        assert "score" in native
        assert "name" in native

    def test_separate_conversions_with_only_custom(self):
        """Test separating when only custom conversions present."""
        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},      # Narwhals custom (vectorized)
            "active": {"cast": "rich_boolean"},    # Narwhals custom (vectorized)
            "description": {"cast": "xml_string"}  # Narwhals custom (vectorized)
        })

        python_only, narwhals, native = config.separate_conversions()

        # All custom types now have Narwhals implementations
        assert len(python_only) == 0
        assert len(narwhals) == 3
        assert len(native) == 0
        assert "amount" in narwhals
        assert "active" in narwhals
        assert "description" in narwhals

    def test_separate_conversions_with_empty_config(self):
        """Test separating with empty config."""
        config = SchemaConfig(columns={})

        python_only, narwhals, native = config.separate_conversions()

        assert len(python_only) == 0
        assert len(narwhals) == 0
        assert len(native) == 0

    def test_separate_conversions_with_no_cast(self):
        """Test separating conversions with only non-cast operations."""
        config = SchemaConfig(columns={
            "name": {"rename": "full_name"},
            "age": {"null_fill": 0},
            "email": {"rename": "email_address", "null_fill": ""}
        })

        python_only, narwhals, native = config.separate_conversions()

        # All operations without cast are native
        assert len(python_only) == 0
        assert len(narwhals) == 0
        assert len(native) == 3
        assert "name" in native
        assert "age" in native
        assert "email" in native

    def test_separate_conversions_preserves_full_spec(self):
        """Test that separate_conversions preserves all spec fields."""
        config = SchemaConfig(columns={
            "amount": {
                "cast": "safe_float",
                "null_fill": 0.0,
                "rename": "total_amount"
            },
            "id": {
                "cast": "integer",
                "rename": "user_id"
            }
        })

        python_only, narwhals, native = config.separate_conversions()

        # Check that full spec is preserved (safe_float is in narwhals now)
        assert narwhals["amount"]["cast"] == "safe_float"
        assert narwhals["amount"]["null_fill"] == 0.0
        assert narwhals["amount"]["rename"] == "total_amount"

        assert native["id"]["cast"] == "integer"
        assert native["id"]["rename"] == "user_id"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
