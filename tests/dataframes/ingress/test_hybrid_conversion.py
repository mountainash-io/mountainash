"""
Integration tests for hybrid conversion strategy in ingress modules.

Tests that the hybrid strategy correctly applies:
- Custom converters at EDGES (Python layer, before DataFrame)
- Native conversions in CENTER (DataFrame layer, vectorized)

This is Phase 2 of the Custom Type Conversion implementation.
"""
import pytest
from dataclasses import dataclass
from typing import Optional
import math

from mountainash.dataframes.schema_config import SchemaConfig, CustomTypeRegistry
from mountainash.dataframes.ingress import PydataConverter


@dataclass
class TestDataClass:
    """Test dataclass for hybrid conversion tests."""
    id: str
    amount: str  # Will be converted to safe_float
    active: str  # Will be converted to rich_boolean
    description: str  # Will be converted to xml_string
    score: str  # Will be converted to integer (native)


class TestHybridConversionDataclass:
    """Test hybrid conversion with dataclass input."""

    def test_hybrid_conversion_custom_and_native(self):
        """Test that custom and native conversions are applied correctly."""
        # Create test data
        data = [
            TestDataClass(
                id="1",
                amount="42.5",
                active="yes",
                description="<tag>value</tag>",
                score="100"
            ),
            TestDataClass(
                id="2",
                amount="99.9",
                active="no",
                description="a&b",
                score="200"
            ),
        ]

        # Create config with both custom and native conversions
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native (vectorized!)
            "amount": {"cast": "safe_float"},    # Custom (at edges)
            "active": {"cast": "rich_boolean"},  # Custom (at edges)
            "description": {"cast": "xml_string"},  # Custom (at edges)
            "score": {"cast": "integer"}         # Native (vectorized!)
        })

        # Convert using hybrid strategy
        df = PydataConverter.convert(data, column_config=config)

        # Verify results
        assert df.shape == (2, 5)

        # Check native conversions (applied in DataFrame, vectorized)
        assert df["id"].dtype.base_type().is_integer()
        assert df["score"].dtype.base_type().is_integer()

        # Check custom conversions (applied at edges, Python layer)
        assert df["amount"][0] == 42.5
        assert df["amount"][1] == 99.9
        assert df["active"][0] is True
        assert df["active"][1] is False
        assert df["description"][0] == "&lt;tag&gt;value&lt;/tag&gt;"
        assert df["description"][1] == "a&amp;b"

    def test_hybrid_conversion_only_custom(self):
        """Test with only custom conversions."""
        data = [
            TestDataClass(
                id="1",
                amount="42.5",
                active="yes",
                description="test",
                score="100"
            ),
        ]

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        df = PydataConverter.convert(data, column_config=config)

        # Custom conversions applied
        assert df["amount"][0] == 42.5
        assert df["active"][0] is True

        # Other columns unchanged
        assert df["id"][0] == "1"
        assert df["score"][0] == "100"

    def test_hybrid_conversion_only_native(self):
        """Test with only native conversions."""
        data = [
            TestDataClass(
                id="1",
                amount="42.5",
                active="yes",
                description="test",
                score="100"
            ),
        ]

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "score": {"cast": "integer"}
        })

        df = PydataConverter.convert(data, column_config=config)

        # Native conversions applied (vectorized)
        assert df["id"].dtype.base_type().is_integer()
        assert df["score"].dtype.base_type().is_integer()
        assert df["id"][0] == 1
        assert df["score"][0] == 100

        # Other columns unchanged
        assert df["amount"][0] == "42.5"
        assert df["active"][0] == "yes"

    def test_hybrid_conversion_with_none_values(self):
        """Test hybrid conversion with None values."""
        @dataclass
        class TestData:
            amount: Optional[str]
            active: Optional[str]

        data = [
            TestData(amount=None, active=None),
            TestData(amount="42.5", active="yes"),
        ]

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        df = PydataConverter.convert(data, column_config=config)

        # None values preserved
        assert df["amount"][0] is None
        assert df["active"][0] is None

        # Non-None values converted
        assert df["amount"][1] == 42.5
        assert df["active"][1] is True

    def test_hybrid_conversion_with_nan_values(self):
        """Test hybrid conversion with NaN values using safe_float."""
        @dataclass
        class TestData:
            amount: float

        data = [
            TestData(amount=float('nan')),
            TestData(amount=42.5),
        ]

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"}
        })

        df = PydataConverter.convert(data, column_config=config)

        # NaN converted to None by safe_float
        assert df["amount"][0] is None
        assert df["amount"][1] == 42.5


class TestHybridConversionPydict:
    """Test hybrid conversion with dict of lists input."""

    def test_hybrid_conversion_pydict_format(self):
        """Test hybrid conversion with columnar data (dict of lists)."""
        data = {
            "id": ["1", "2", "3"],
            "amount": ["42.5", "99.9", "12.3"],
            "active": ["yes", "no", "true"],
            "score": ["100", "200", "300"]
        }

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native
            "amount": {"cast": "safe_float"},    # Custom
            "active": {"cast": "rich_boolean"},  # Custom
            "score": {"cast": "integer"}         # Native
        })

        df = PydataConverter.convert(data, column_config=config)

        # Verify results
        assert df.shape == (3, 4)

        # Native conversions
        assert df["id"].dtype.base_type().is_integer()
        assert df["score"].dtype.base_type().is_integer()

        # Custom conversions
        assert list(df["amount"]) == [42.5, 99.9, 12.3]
        assert list(df["active"]) == [True, False, True]


class TestHybridConversionPylist:
    """Test hybrid conversion with list of dicts input."""

    def test_hybrid_conversion_pylist_format(self):
        """Test hybrid conversion with row data (list of dicts)."""
        data = [
            {"id": "1", "amount": "42.5", "active": "yes"},
            {"id": "2", "amount": "99.9", "active": "no"},
            {"id": "3", "amount": "12.3", "active": "1"},
        ]

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native
            "amount": {"cast": "safe_float"},    # Custom
            "active": {"cast": "rich_boolean"}   # Custom
        })

        df = PydataConverter.convert(data, column_config=config)

        # Verify results
        assert df.shape == (3, 3)

        # Native conversions
        assert df["id"].dtype.base_type().is_integer()
        assert list(df["id"]) == [1, 2, 3]

        # Custom conversions
        assert list(df["amount"]) == [42.5, 99.9, 12.3]
        assert list(df["active"]) == [True, False, True]


class TestHybridConversionMixedOperations:
    """Test hybrid conversion with mixed operations (cast, rename, null_fill)."""

    def test_hybrid_with_rename(self):
        """Test hybrid conversion with column renaming."""
        data = [
            {"old_amount": "42.5", "old_id": "1"},
            {"old_amount": "99.9", "old_id": "2"},
        ]

        config = SchemaConfig(columns={
            "old_amount": {"cast": "safe_float", "rename": "amount"},
            "old_id": {"cast": "integer", "rename": "id"}
        })

        df = PydataConverter.convert(data, column_config=config)

        # Columns renamed
        assert "amount" in df.columns
        assert "id" in df.columns
        assert "old_amount" not in df.columns
        assert "old_id" not in df.columns

        # Conversions applied
        assert df["amount"][0] == 42.5
        assert df["id"].dtype.base_type().is_integer()

    def test_hybrid_with_null_fill(self):
        """Test hybrid conversion with null filling."""
        data = [
            {"amount": None, "score": None},
            {"amount": "42.5", "score": "100"},
        ]

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float", "null_fill": 0.0},
            "score": {"cast": "integer", "null_fill": 0}
        })

        df = PydataConverter.convert(data, column_config=config)

        # Null values filled
        # Note: safe_float returns None for None input, then null_fill should apply
        # But we need to check if null_fill works correctly here
        assert df["score"][0] == 0  # Native null_fill
        assert df["score"][1] == 100


class TestSeparateConversionsHelper:
    """Test the separate_conversions() method that enables hybrid strategy."""

    def test_separate_conversions_correctly(self):
        """Test that separate_conversions correctly identifies custom vs native."""
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native
            "amount": {"cast": "safe_float"},    # Narwhals custom (vectorized)
            "name": {"rename": "full_name"},     # Native (no cast)
            "active": {"cast": "rich_boolean"}   # Narwhals custom (vectorized)
        })

        python_only, narwhals, native = config.separate_conversions()

        # Verify Narwhals custom conversions (vectorized)
        assert "amount" in narwhals
        assert "active" in narwhals
        assert len(narwhals) == 2

        # Verify no Python-only custom
        assert len(python_only) == 0

        # Verify native conversions
        assert "id" in native
        assert "name" in native
        assert len(native) == 2

    def test_separate_conversions_preserves_full_spec(self):
        """Test that separate_conversions preserves all spec fields."""
        config = SchemaConfig(columns={
            "amount": {
                "cast": "safe_float",
                "rename": "total_amount",
                "null_fill": 0.0
            }
        })

        python_only, narwhals, native = config.separate_conversions()

        # Full spec preserved in Narwhals custom conversions (safe_float is vectorized)
        assert narwhals["amount"]["cast"] == "safe_float"
        assert narwhals["amount"]["rename"] == "total_amount"
        assert narwhals["amount"]["null_fill"] == 0.0


class TestPerformanceCharacteristics:
    """
    Test performance characteristics of hybrid strategy.

    Note: These are not strict performance tests, just verification
    that the hybrid strategy is working as expected.
    """

    def test_large_dataset_with_custom_types(self):
        """Test hybrid strategy with larger dataset."""
        # Create a larger dataset
        n_rows = 1000
        data = [
            {"id": str(i), "amount": str(float(i) * 1.5), "active": "yes" if i % 2 == 0 else "no"}
            for i in range(n_rows)
        ]

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native (vectorized, FAST!)
            "amount": {"cast": "safe_float"},    # Custom (at edges)
            "active": {"cast": "rich_boolean"}   # Custom (at edges)
        })

        df = PydataConverter.convert(data, column_config=config)

        # Verify all conversions applied correctly
        assert df.shape == (n_rows, 3)
        assert df["id"].dtype.base_type().is_integer()
        assert all(isinstance(val, (int, float)) for val in df["amount"])
        assert all(isinstance(val, bool) for val in df["active"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
