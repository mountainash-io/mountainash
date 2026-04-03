"""
Tests for mountainash.typespec.custom_types.

Covers:
- CustomTypeRegistry CRUD operations
- safe_float Python converter
- safe_int Python converter
- xml_string Python converter
- rich_boolean Python converter
- Built-in vectorized converters (narwhals implementations)
- User-defined converter registration/unregistration
"""
from __future__ import annotations

import pytest

from mountainash.typespec.custom_types import (
    CustomTypeRegistry,
    TypeConverterSpec,
    _register_standard_converters,
)


# ============================================================================
# TestCustomTypeRegistryCRUD
# ============================================================================

class TestCustomTypeRegistryCRUD:
    """Basic CRUD operations on CustomTypeRegistry."""

    def test_register_and_has(self, clean_custom_registry):
        reg = clean_custom_registry
        reg.register(
            name="test_type",
            target_universal_type="string",
            python_converter=lambda v, field_name=None: str(v) if v is not None else None,
        )
        assert reg.has_converter("test_type") is True

    def test_unregister_returns_true_when_found(self, clean_custom_registry):
        reg = clean_custom_registry
        reg.register(
            name="to_remove",
            target_universal_type="string",
            python_converter=lambda v, field_name=None: v,
        )
        result = reg.unregister("to_remove")
        assert result is True
        assert reg.has_converter("to_remove") is False

    def test_unregister_returns_false_when_not_found(self, clean_custom_registry):
        reg = clean_custom_registry
        result = reg.unregister("does_not_exist")
        assert result is False

    def test_get_spec_returns_spec_when_registered(self, clean_custom_registry):
        reg = clean_custom_registry

        def my_conv(v, field_name=None):
            return v

        reg.register(name="my_type", target_universal_type="string", python_converter=my_conv)
        spec = reg.get_spec("my_type")
        assert spec is not None
        assert isinstance(spec, TypeConverterSpec)
        assert spec.name == "my_type"

    def test_get_spec_returns_none_when_not_registered(self, clean_custom_registry):
        reg = clean_custom_registry
        spec = reg.get_spec("not_registered")
        assert spec is None

    def test_list_converters(self, clean_custom_registry):
        reg = clean_custom_registry
        reg.register(
            name="a_type",
            target_universal_type="string",
            python_converter=lambda v, field_name=None: v,
            description="A type",
        )
        listing = reg.list_converters()
        assert "a_type" in listing
        assert listing["a_type"] == "A type"

    def test_clear_removes_all(self, clean_custom_registry):
        reg = clean_custom_registry
        _register_standard_converters()
        reg.clear()
        assert reg.list_converters() == {}

    def test_duplicate_registration_raises(self, clean_custom_registry):
        reg = clean_custom_registry
        reg.register(
            name="dup",
            target_universal_type="string",
            python_converter=lambda v, field_name=None: v,
        )
        with pytest.raises(ValueError, match="already registered"):
            reg.register(
                name="dup",
                target_universal_type="string",
                python_converter=lambda v, field_name=None: v,
            )

    def test_is_native_type_for_universal(self):
        """Standard UniversalType values should be reported as native."""
        assert CustomTypeRegistry.is_native_type("integer") is True
        assert CustomTypeRegistry.is_native_type("string") is True
        assert CustomTypeRegistry.is_native_type("number") is True

    def test_is_native_type_false_for_custom(self, clean_custom_registry):
        reg = clean_custom_registry
        _register_standard_converters()
        assert reg.is_native_type("safe_float") is False


# ============================================================================
# TestSafeFloatPython
# ============================================================================

class TestSafeFloatPython:
    """Python-layer safe_float conversion tests."""

    def setup_method(self):
        _register_standard_converters()

    def test_plain_float(self):
        assert CustomTypeRegistry.convert(3.14, "safe_float") == pytest.approx(3.14)

    def test_string_float(self):
        assert CustomTypeRegistry.convert("3.14", "safe_float") == pytest.approx(3.14)

    def test_nan_becomes_none(self):
        assert CustomTypeRegistry.convert(float("nan"), "safe_float") is None

    def test_none_stays_none(self):
        assert CustomTypeRegistry.convert(None, "safe_float") is None

    def test_integer_becomes_float(self):
        result = CustomTypeRegistry.convert(42, "safe_float")
        assert result == pytest.approx(42.0)
        assert isinstance(result, float)


# ============================================================================
# TestSafeIntPython
# ============================================================================

class TestSafeIntPython:
    """Python-layer safe_int conversion tests."""

    def setup_method(self):
        _register_standard_converters()

    def test_plain_int(self):
        assert CustomTypeRegistry.convert(42, "safe_int") == 42

    def test_string_int(self):
        assert CustomTypeRegistry.convert("42", "safe_int") == 42

    def test_nan_becomes_none(self):
        assert CustomTypeRegistry.convert(float("nan"), "safe_int") is None

    def test_none_stays_none(self):
        assert CustomTypeRegistry.convert(None, "safe_int") is None

    def test_float_truncates(self):
        result = CustomTypeRegistry.convert(3.7, "safe_int")
        assert result == 3


# ============================================================================
# TestXmlStringPython
# ============================================================================

class TestXmlStringPython:
    """Python-layer xml_string conversion tests."""

    def setup_method(self):
        _register_standard_converters()

    def test_lt_escaped(self):
        assert CustomTypeRegistry.convert("<tag>", "xml_string") == "&lt;tag&gt;"

    def test_amp_escaped(self):
        assert CustomTypeRegistry.convert("A&B", "xml_string") == "A&amp;B"

    def test_none_stays_none(self):
        assert CustomTypeRegistry.convert(None, "xml_string") is None


# ============================================================================
# TestRichBooleanPython
# ============================================================================

_RICH_BOOL_CASES = [
    ("yes", True),
    ("no", False),
    ("true", True),
    ("false", False),
    ("1", True),
    ("0", False),
    (True, True),
    (False, False),
    (1, True),
    (0, False),
    (None, None),
]


class TestRichBooleanPython:
    """Python-layer rich_boolean conversion tests."""

    def setup_method(self):
        _register_standard_converters()

    @pytest.mark.parametrize("value,expected", _RICH_BOOL_CASES)
    def test_known_values(self, value, expected):
        result = CustomTypeRegistry.convert(value, "rich_boolean")
        assert result is expected

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            CustomTypeRegistry.convert("maybe", "rich_boolean")


# ============================================================================
# TestBuiltinVectorized
# ============================================================================

class TestBuiltinVectorized:
    """All 4 standard converters should have Narwhals vectorized implementations."""

    def setup_method(self):
        _register_standard_converters()

    @pytest.mark.parametrize("name", ["safe_float", "safe_int", "xml_string", "rich_boolean"])
    def test_is_vectorized(self, name):
        assert CustomTypeRegistry.is_vectorized(name) is True

    @pytest.mark.parametrize("name", ["safe_float", "safe_int", "xml_string", "rich_boolean"])
    def test_get_narwhals_converter_is_not_none(self, name):
        conv = CustomTypeRegistry.get_narwhals_converter(name)
        assert conv is not None
        assert callable(conv)


# ============================================================================
# TestUserDefinedConverter
# ============================================================================

class TestUserDefinedConverter:
    """Register a Python-only converter and verify its behaviour."""

    def test_register_python_only_is_not_vectorized(self, clean_custom_registry):
        reg = clean_custom_registry

        def my_upper(v, field_name=None):
            return str(v).upper() if v is not None else None

        reg.register(
            name="upper_string",
            target_universal_type="string",
            python_converter=my_upper,
        )
        assert reg.is_vectorized("upper_string") is False

    def test_convert_calls_python_converter(self, clean_custom_registry):
        reg = clean_custom_registry

        def my_upper(v, field_name=None):
            return str(v).upper() if v is not None else None

        reg.register(
            name="upper_string",
            target_universal_type="string",
            python_converter=my_upper,
        )
        assert reg.convert("hello", "upper_string") == "HELLO"
        assert reg.convert(None, "upper_string") is None

    def test_unregister_removes_converter(self, clean_custom_registry):
        reg = clean_custom_registry
        reg.register(
            name="temp_type",
            target_universal_type="string",
            python_converter=lambda v, field_name=None: v,
        )
        reg.unregister("temp_type")
        assert reg.has_converter("temp_type") is False
