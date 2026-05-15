"""Tests for the three-tier hybrid conversion strategy (TypeSpec/FieldSpec API)."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.ingress.custom_type_helpers import (
    _apply_narwhals_custom_converters,
    apply_custom_converters_to_dict,
    apply_custom_converters_to_dicts,
    apply_hybrid_conversion,
    apply_native_conversions_to_dataframe,
    separate_conversions,
)
from mountainash.typespec.custom_types import CustomTypeRegistry, _register_standard_converters
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def ensure_standard_converters():
    """Ensure standard converters are registered before each test."""
    _register_standard_converters()


# ---------------------------------------------------------------------------
# TestSeparateConversions
# ---------------------------------------------------------------------------


class TestSeparateConversions:
    """Tests for the standalone separate_conversions() function."""

    def test_native_integer(self):
        """A field with type=INTEGER and no custom_cast goes to native tier."""
        spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
        python_only, narwhals, native = separate_conversions(spec)
        assert "id" in native
        assert "id" not in python_only
        assert "id" not in narwhals

    def test_custom_safe_float_is_narwhals(self):
        """safe_float has a Narwhals converter → goes to narwhals tier."""
        spec = TypeSpec(fields=[FieldSpec(name="amount", custom_cast="safe_float")])
        python_only, narwhals, native = separate_conversions(spec)
        assert "amount" in narwhals
        assert "amount" not in python_only
        assert "amount" not in native

    def test_no_cast_is_native(self):
        """Field with no cast type goes to native (nothing to do but pass through)."""
        spec = TypeSpec(fields=[FieldSpec(name="label")])
        python_only, narwhals, native = separate_conversions(spec)
        assert "label" in native
        assert "label" not in python_only
        assert "label" not in narwhals

    def test_mixed_routing(self):
        """Mixed spec routes each field to the correct tier."""
        spec = TypeSpec(
            fields=[
                FieldSpec(name="amount", custom_cast="safe_float"),   # → narwhals
                FieldSpec(name="id", type=UniversalType.INTEGER),      # → native
                FieldSpec(name="tag", rename_from="label"),            # → native
            ]
        )
        python_only, narwhals, native = separate_conversions(spec)

        assert "amount" in narwhals
        # tag is stored under source_name "label"
        assert "label" in native
        assert "id" in native
        assert len(python_only) == 0

    def test_python_only_converter_goes_to_python_only(self):
        """A custom_cast with no Narwhals implementation goes to python_only."""
        # Register a Python-only converter for this test
        def _dummy(value, *, field_name=None):
            return value

        name = "_test_python_only_dummy_"
        if not CustomTypeRegistry.has_converter(name):
            CustomTypeRegistry.register(
                name=name,
                target_universal_type="string",
                python_converter=_dummy,
                description="Test Python-only converter",
            )

        try:
            spec = TypeSpec(fields=[FieldSpec(name="col", custom_cast=name)])
            python_only, narwhals, native = separate_conversions(spec)
            assert "col" in python_only
            assert "col" not in narwhals
            assert "col" not in native
        finally:
            CustomTypeRegistry.unregister(name)


# ---------------------------------------------------------------------------
# TestTier3PythonEdge
# ---------------------------------------------------------------------------


class TestTier3PythonEdge:
    """Tests for apply_custom_converters_to_dict and apply_custom_converters_to_dicts."""

    def test_single_dict_safe_float(self):
        """safe_float converter on 'amount' field converts string to float."""
        field = FieldSpec(name="amount", custom_cast="safe_float")
        custom_conversions = {"amount": field}
        data = {"amount": "42.5", "id": "123", "name": "Alice"}
        result = apply_custom_converters_to_dict(data, custom_conversions)
        assert result["amount"] == 42.5
        assert isinstance(result["amount"], float)
        # Other fields untouched
        assert result["id"] == "123"
        assert result["name"] == "Alice"

    def test_list_of_dicts(self):
        """safe_float converter applied to multiple rows."""
        field = FieldSpec(name="amount", custom_cast="safe_float")
        custom_conversions = {"amount": field}
        data = [
            {"amount": "10.0", "label": "a"},
            {"amount": "99.9", "label": "b"},
            {"amount": "0.5", "label": "c"},
        ]
        result = apply_custom_converters_to_dicts(data, custom_conversions)
        assert len(result) == 3
        assert result[0]["amount"] == 10.0
        assert result[1]["amount"] == 99.9
        assert result[2]["amount"] == 0.5
        assert result[0]["label"] == "a"

    def test_empty_conversions_passthrough(self):
        """Empty conversions dict returns data unchanged (no FieldSpec applied)."""
        data = {"amount": "42.5", "id": "123"}
        result = apply_custom_converters_to_dict(data, {})
        assert result == data

    def test_empty_conversions_list_passthrough(self):
        """Empty conversions on list of dicts returns same list (short-circuit)."""
        data = [{"amount": "42.5"}, {"amount": "10.0"}]
        result = apply_custom_converters_to_dicts(data, {})
        assert result is data  # Short-circuit returns same object

    def test_none_value_safe_float(self):
        """safe_float handles None value without error."""
        field = FieldSpec(name="amount", custom_cast="safe_float")
        custom_conversions = {"amount": field}
        data = {"amount": None, "id": "1"}
        result = apply_custom_converters_to_dict(data, custom_conversions)
        assert result["amount"] is None
        assert result["id"] == "1"


# ---------------------------------------------------------------------------
# TestTier1NativeDataFrame
# ---------------------------------------------------------------------------


class TestTier1NativeDataFrame:
    """Tests for apply_native_conversions_to_dataframe."""

    def test_integer_cast(self):
        """String column cast to integer via native conversions."""
        df = pl.DataFrame({"id": ["1", "2", "3"], "name": ["a", "b", "c"]})
        field = FieldSpec(name="id", type=UniversalType.INTEGER)
        native_conversions = {"id": field}
        result = apply_native_conversions_to_dataframe(df, native_conversions)
        assert result["id"].dtype == pl.Int64

    def test_empty_conversions_passthrough(self):
        """Empty native conversions returns DataFrame unchanged."""
        df = pl.DataFrame({"id": ["1", "2"], "name": ["a", "b"]})
        result = apply_native_conversions_to_dataframe(df, {})
        assert result.schema == df.schema
        assert result.shape == df.shape


# ---------------------------------------------------------------------------
# TestTier2NarwhalsVectorized
# ---------------------------------------------------------------------------


class TestTier2NarwhalsVectorized:
    """Tests for _apply_narwhals_custom_converters."""

    def test_safe_float_vectorized(self):
        """safe_float via Narwhals converts string column to Float64."""
        df = pl.DataFrame({"amount": ["1.5", "2.7", "10.0"]})
        field = FieldSpec(name="amount", custom_cast="safe_float")
        narwhals_custom = {"amount": field}
        result = _apply_narwhals_custom_converters(df, narwhals_custom)
        assert result["amount"].dtype == pl.Float64
        assert result["amount"].to_list() == [1.5, 2.7, 10.0]

    def test_safe_float_vectorized_with_none(self):
        """safe_float via Narwhals converts NaN values to None."""
        df = pl.DataFrame({"amount": ["1.5", None, "3.0"]})
        field = FieldSpec(name="amount", custom_cast="safe_float")
        narwhals_custom = {"amount": field}
        result = _apply_narwhals_custom_converters(df, narwhals_custom)
        assert result["amount"].dtype == pl.Float64
        vals = result["amount"].to_list()
        assert vals[0] == 1.5
        assert vals[1] is None
        assert vals[2] == 3.0


# ---------------------------------------------------------------------------
# TestHybridEndToEnd
# ---------------------------------------------------------------------------


class TestHybridEndToEnd:
    """Tests for apply_hybrid_conversion (full pipeline)."""

    def test_native_only(self):
        """TypeSpec with integer cast produces correct dtype."""
        spec = TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="name", type=UniversalType.STRING),
            ],
        )
        data = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        df = apply_hybrid_conversion(data, spec)
        assert isinstance(df, pl.DataFrame)
        assert df["id"].dtype == pl.Int64
        assert df["name"].to_list() == ["Alice", "Bob"]

    def test_no_spec_creates_dataframe(self):
        """None spec just creates DataFrame from dicts."""
        data = [{"x": 1, "y": "hello"}, {"x": 2, "y": "world"}]
        df = apply_hybrid_conversion(data, None)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 2)
        assert set(df.columns) == {"x", "y"}

    def test_safe_float_end_to_end(self):
        """apply_hybrid_conversion with safe_float produces Float64 column."""
        spec = TypeSpec(
            fields=[
                FieldSpec(name="price", custom_cast="safe_float"),
                FieldSpec(name="name", type=UniversalType.STRING),
            ],
        )
        data = [{"price": "9.99", "name": "Widget"}, {"price": "4.50", "name": "Gizmo"}]
        df = apply_hybrid_conversion(data, spec)
        assert df["price"].dtype == pl.Float64
        assert df["price"].to_list() == [9.99, 4.50]

    def test_tier_assignment(self):
        """separate_conversions routes safe_float to narwhals, integer to native."""
        spec = TypeSpec(
            fields=[
                FieldSpec(name="amount", custom_cast="safe_float"),
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(name="tag", rename_from="label"),
            ],
        )
        python_only, narwhals_custom, native = separate_conversions(spec)

        # safe_float is vectorized → narwhals tier
        assert "amount" in narwhals_custom

        # integer → native tier
        assert "id" in native

        # rename (source_name is "label") → native tier
        assert "label" in native

        # safe_float must NOT be in python_only
        assert "amount" not in python_only
