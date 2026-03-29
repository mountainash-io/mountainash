"""Tests for the three-tier hybrid conversion strategy."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.pydata.ingress.custom_type_helpers import (
    apply_custom_converters_to_dict,
    apply_custom_converters_to_dicts,
    apply_hybrid_conversion,
    apply_native_conversions_to_dataframe,
    _apply_narwhals_custom_converters,
)
from mountainash.schema.config.custom_types import _register_standard_converters
from mountainash.schema.config.schema_config import SchemaConfig


# ---------------------------------------------------------------------------
# Ensure standard converters are registered
# ---------------------------------------------------------------------------

_register_standard_converters()


# ---------------------------------------------------------------------------
# TestTier3PythonEdge
# ---------------------------------------------------------------------------


class TestTier3PythonEdge:
    """Tests for apply_custom_converters_to_dict and apply_custom_converters_to_dicts."""

    def test_single_dict_safe_float(self):
        """safe_float converter on 'amount' field converts string to float."""
        custom_conversions = {"amount": {"cast": "safe_float"}}
        data = {"amount": "42.5", "id": "123", "name": "Alice"}
        result = apply_custom_converters_to_dict(data, custom_conversions)
        assert result["amount"] == 42.5
        assert isinstance(result["amount"], float)
        # Other fields untouched
        assert result["id"] == "123"
        assert result["name"] == "Alice"

    def test_list_of_dicts_safe_float(self):
        """safe_float converter applied to multiple rows."""
        custom_conversions = {"amount": {"cast": "safe_float"}}
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
        # Other fields untouched
        assert result[0]["label"] == "a"

    def test_empty_conversions_passthrough(self):
        """Empty conversions dict returns data unchanged."""
        data = {"amount": "42.5", "id": "123"}
        result = apply_custom_converters_to_dict(data, {})
        assert result == data

    def test_empty_conversions_list_passthrough(self):
        """Empty conversions on list of dicts returns data unchanged."""
        data = [{"amount": "42.5"}, {"amount": "10.0"}]
        result = apply_custom_converters_to_dicts(data, {})
        # Returns same list (short-circuit)
        assert result == data

    def test_single_dict_none_value_safe_float(self):
        """safe_float handles None value without error."""
        custom_conversions = {"amount": {"cast": "safe_float"}}
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
        native_conversions = {"id": {"cast": "integer"}}
        result = apply_native_conversions_to_dataframe(df, native_conversions)
        assert result["id"].dtype == pl.Int64

    def test_empty_conversions_passthrough(self):
        """Empty native conversions returns DataFrame unchanged."""
        df = pl.DataFrame({"id": ["1", "2"], "name": ["a", "b"]})
        result = apply_native_conversions_to_dataframe(df, {})
        assert result.schema == df.schema
        assert result.shape == df.shape

    def test_unknown_column_skipped(self):
        """Conversion spec for a column not in DataFrame is silently skipped."""
        df = pl.DataFrame({"id": ["1", "2"]})
        native_conversions = {"missing_col": {"cast": "integer"}}
        result = apply_native_conversions_to_dataframe(df, native_conversions)
        # DataFrame unchanged
        assert "missing_col" not in result.columns
        assert result["id"].dtype == pl.String


# ---------------------------------------------------------------------------
# TestTier2NarwhalsVectorized
# ---------------------------------------------------------------------------


class TestTier2NarwhalsVectorized:
    """Tests for _apply_narwhals_custom_converters."""

    def test_safe_float_vectorized(self):
        """safe_float via Narwhals converts string column to Float64."""
        df = pl.DataFrame({"amount": ["1.5", "2.7", "10.0"]})
        narwhals_custom = {"amount": {"cast": "safe_float"}}
        result = _apply_narwhals_custom_converters(df, narwhals_custom)
        assert result["amount"].dtype == pl.Float64
        assert result["amount"].to_list() == [1.5, 2.7, 10.0]

    def test_safe_float_vectorized_with_none(self):
        """safe_float via Narwhals converts NaN values to None."""
        df = pl.DataFrame({"amount": ["1.5", None, "3.0"]})
        narwhals_custom = {"amount": {"cast": "safe_float"}}
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
        """SchemaConfig with integer cast produces correct dtype."""
        config = SchemaConfig(
            columns={"id": {"cast": "integer"}},
            keep_only_mapped=False,
            strict=False,
        )
        data = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        df = apply_hybrid_conversion(data, config)
        assert isinstance(df, pl.DataFrame)
        assert df["id"].dtype == pl.Int64
        assert df["name"].to_list() == ["Alice", "Bob"]

    def test_no_config_creates_dataframe(self):
        """None config just creates DataFrame from dicts."""
        data = [{"x": 1, "y": "hello"}, {"x": 2, "y": "world"}]
        df = apply_hybrid_conversion(data, None)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (2, 2)
        assert set(df.columns) == {"x", "y"}

    def test_tier_assignment_separate_conversions(self):
        """separate_conversions puts safe_float in narwhals_custom, integer in native."""
        config = SchemaConfig(
            columns={
                "amount": {"cast": "safe_float"},
                "id": {"cast": "integer"},
                "label": {"rename": "tag"},
            },
            keep_only_mapped=False,
            strict=False,
        )
        python_custom, narwhals_custom, native = config.separate_conversions()

        # safe_float is vectorized → goes into narwhals_custom
        assert "amount" in narwhals_custom

        # integer is native
        assert "id" in native

        # rename is a native operation
        assert "label" in native

        # safe_float should NOT be in native casts
        assert "amount" not in python_custom

    def test_safe_float_end_to_end(self):
        """apply_hybrid_conversion with safe_float produces Float64 column."""
        config = SchemaConfig(
            columns={"price": {"cast": "safe_float"}},
            keep_only_mapped=False,
            strict=False,
        )
        data = [{"price": "9.99", "name": "Widget"}, {"price": "4.50", "name": "Gizmo"}]
        df = apply_hybrid_conversion(data, config)
        assert df["price"].dtype == pl.Float64
        assert df["price"].to_list() == [9.99, 4.50]
