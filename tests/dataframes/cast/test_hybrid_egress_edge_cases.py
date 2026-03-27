"""
Edge cases and error handling tests for hybrid egress custom type conversion.

Tests:
- Error handling for invalid custom types
- Converter failures and recovery
- Empty DataFrames
- Edge values (infinity, very large numbers, etc.)
- Performance with large datasets
"""
import pytest
from dataclasses import dataclass
from typing import Optional
import polars as pl
import math

from mountainash.dataframes.schema_config import SchemaConfig, CustomTypeRegistry
from mountainash.dataframes.cast import DataFrameCastFactory


class TestErrorHandling:
    """Test error handling in hybrid egress."""

    def test_invalid_custom_type_name(self):
        """Test that invalid custom type names are handled gracefully."""
        @dataclass
        class TestData:
            amount: float

        df = pl.DataFrame({
            "amount": ["42.5", "99.9"]
        })

        # Use a non-existent custom type
        config = SchemaConfig(columns={
            "amount": {"cast": "nonexistent_custom_type"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        # Should not raise error if raise_on_error=False (default)
        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Values should remain as strings (unconverted)
        assert isinstance(result[0].amount, str)
        assert result[0].amount == "42.5"

    def test_custom_converter_with_invalid_data(self):
        """Test custom converter behavior with invalid data."""
        @dataclass
        class TestData:
            amount: Optional[float]

        df = pl.DataFrame({
            "amount": ["not_a_number", "42.5"]
        })

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # safe_float should convert invalid values to None
        assert result[0].amount is None
        assert result[1].amount == 42.5

    def test_rich_boolean_with_ambiguous_values(self):
        """Test rich_boolean converter with ambiguous/invalid values."""
        @dataclass
        class TestData:
            active: Optional[bool]

        df = pl.DataFrame({
            "active": ["yes", "maybe", "no", "sometimes"]
        })

        config = SchemaConfig(columns={
            "active": {"cast": "rich_boolean"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # "yes" -> True, "no" -> False, invalid -> None
        assert result[0].active is True
        assert result[1].active is None  # "maybe" is invalid
        assert result[2].active is False
        assert result[3].active is None  # "sometimes" is invalid


class TestEdgeCases:
    """Test edge cases for hybrid egress."""

    def test_empty_dataframe(self):
        """Test egress with empty DataFrame."""
        @dataclass
        class TestData:
            id: int
            amount: float
            active: bool

        # Create empty DataFrame with correct schema
        df = pl.DataFrame({
            "id": pl.Series([], dtype=pl.Utf8),
            "amount": pl.Series([], dtype=pl.Utf8),
            "active": pl.Series([], dtype=pl.Utf8)
        })

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Should return empty list
        assert result == []

    def test_all_null_column(self):
        """Test egress with column containing only null values."""
        @dataclass
        class TestData:
            id: int
            amount: Optional[float]
            active: Optional[bool]

        df = pl.DataFrame({
            "id": ["1", "2", "3"],
            "amount": [None, None, None],
            "active": [None, None, None]
        })

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # All custom type columns should be None
        assert len(result) == 3
        assert result[0].id == 1
        assert result[0].amount is None
        assert result[0].active is None

    def test_safe_float_with_infinity(self):
        """Test safe_float converter with infinity values."""
        @dataclass
        class TestData:
            value: Optional[float]

        df = pl.DataFrame({
            "value": [float('inf'), float('-inf'), "42.5"]
        })

        config = SchemaConfig(columns={
            "value": {"cast": "safe_float"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # safe_float converts inf/nan to None
        assert result[0].value is None  # inf -> None
        assert result[1].value is None  # -inf -> None
        assert result[2].value == 42.5

    def test_safe_float_with_very_large_numbers(self):
        """Test safe_float with very large floating point numbers."""
        @dataclass
        class TestData:
            value: float

        df = pl.DataFrame({
            "value": ["1.7976931348623157e+308", "42.5", "2.2250738585072014e-308"]
        })

        config = SchemaConfig(columns={
            "value": {"cast": "safe_float"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Should handle very large and very small numbers
        assert result[0].value == 1.7976931348623157e+308
        assert result[1].value == 42.5
        assert result[2].value == 2.2250738585072014e-308

    def test_safe_int_with_overflow(self):
        """Test safe_int with values that would overflow."""
        @dataclass
        class TestData:
            value: Optional[int]

        # Very large number that exceeds typical int range
        df = pl.DataFrame({
            "value": ["999999999999999999999999999999", "42", "invalid"]
        })

        config = SchemaConfig(columns={
            "value": {"cast": "safe_int"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Python ints can handle arbitrarily large values
        assert result[0].value == 999999999999999999999999999999
        assert result[1].value == 42
        assert result[2].value is None  # Invalid -> None

    def test_xml_string_with_complex_html(self):
        """Test xml_string with complex HTML/XML structures."""
        @dataclass
        class TestData:
            content: str

        df = pl.DataFrame({
            "content": [
                "<div class='test' id=\"123\">Content & \"quotes\"</div>",
                "Plain text with <brackets> and & ampersands",
                "<script>alert('XSS')</script>"
            ]
        })

        config = SchemaConfig(columns={
            "content": {"cast": "xml_string"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # All special characters should be escaped
        assert "&lt;div" in result[0].content
        assert "&amp;" in result[0].content
        assert "&quot;" in result[0].content
        assert "&lt;script&gt;" in result[2].content

    def test_single_row_dataframe(self):
        """Test egress with single-row DataFrame."""
        @dataclass
        class TestData:
            id: int
            amount: float
            active: bool

        df = pl.DataFrame({
            "id": ["1"],
            "amount": ["42.5"],
            "active": ["yes"]
        })

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].amount == 42.5
        assert result[0].active is True

    def test_mixed_valid_invalid_data(self):
        """Test DataFrame with mix of valid and invalid data for custom types."""
        @dataclass
        class TestData:
            amount: Optional[float]
            active: Optional[bool]

        df = pl.DataFrame({
            "amount": ["42.5", "invalid", "99.9", None],
            "active": ["yes", "maybe", "no", None]
        })

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Valid values converted, invalid -> None
        assert result[0].amount == 42.5
        assert result[0].active is True

        assert result[1].amount is None  # Invalid
        assert result[1].active is None  # Invalid

        assert result[2].amount == 99.9
        assert result[2].active is False

        assert result[3].amount is None  # None
        assert result[3].active is None  # None


class TestPerformanceEdgeCases:
    """Test performance characteristics with edge cases."""

    def test_very_wide_dataframe(self):
        """Test egress with DataFrame with many columns."""
        @dataclass
        class WideData:
            col_0: int
            col_1: float
            col_2: float
            col_3: float
            col_4: float
            col_5: float
            col_6: float
            col_7: float
            col_8: float
            col_9: float

        # Create wide DataFrame
        data = {
            "col_0": ["1", "2"]
        }
        for i in range(1, 10):
            data[f"col_{i}"] = [str(float(i) * 10.5), str(float(i) * 20.5)]

        df = pl.DataFrame(data)

        # Config with mix of native and custom
        config_dict = {"col_0": {"cast": "integer"}}
        for i in range(1, 10):
            config_dict[f"col_{i}"] = {"cast": "safe_float"}

        config = SchemaConfig(columns=config_dict)

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            WideData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Verify all columns converted correctly
        assert len(result) == 2
        assert result[0].col_0 == 1
        assert result[0].col_1 == 10.5
        assert result[0].col_9 == 90.5

    def test_large_string_values(self):
        """Test custom converters with very large string values."""
        @dataclass
        class TestData:
            content: str

        # Create very large XML string
        large_xml = "<root>" + ("x" * 10000) + "</root>"

        df = pl.DataFrame({
            "content": [large_xml, "small"]
        })

        config = SchemaConfig(columns={
            "content": {"cast": "xml_string"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Should handle large strings
        assert "&lt;root&gt;" in result[0].content
        assert "x" * 10000 in result[0].content
        assert result[1].content == "small"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
