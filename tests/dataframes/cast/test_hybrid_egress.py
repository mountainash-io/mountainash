"""
Integration tests for hybrid conversion strategy in egress (DataFrame → Python data).

Tests that the hybrid strategy correctly applies:
- Native conversions in CENTER (DataFrame layer, vectorized)
- Custom converters at EDGES (Python layer, after extraction)

This is Phase 3 of the Custom Type Conversion implementation.
"""
import pytest
from dataclasses import dataclass
from typing import Optional
import polars as pl

from mountainash.dataframes.schema_config import SchemaConfig
from mountainash.dataframes.cast import DataFrameCastFactory


@dataclass
class UserDataclass:
    """Test dataclass for hybrid egress tests."""
    id: int
    amount: float
    active: bool
    description: str


class TestHybridEgressDataclass:
    """Test hybrid egress conversion to dataclass."""

    def test_hybrid_egress_custom_and_native(self):
        """Test that custom and native conversions are applied correctly in egress."""
        # Create test DataFrame
        df = pl.DataFrame({
            "id": ["1", "2", "3"],
            "amount": ["42.5", "99.9", "12.3"],
            "active": ["yes", "no", "true"],
            "description": ["<tag>value</tag>", "a&b", "test"]
        })

        # Create config with both custom and native conversions
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native (vectorized in DF!)
            "amount": {"cast": "safe_float"},    # Custom (after extraction)
            "active": {"cast": "rich_boolean"},  # Custom (after extraction)
            "description": {"cast": "xml_string"}  # Custom (after extraction)
        })

        # Convert using hybrid egress strategy
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            UserDataclass,
            schema_config=config,
            auto_derive_schema=False
        )

        # Verify results
        assert len(result) == 3

        # Check first record
        assert isinstance(result[0], UserDataclass)
        assert result[0].id == 1  # Native conversion
        assert result[0].amount == 42.5  # Custom conversion
        assert result[0].active is True  # Custom conversion
        assert result[0].description == "&lt;tag&gt;value&lt;/tag&gt;"  # Custom conversion

        # Check second record
        assert result[1].id == 2
        assert result[1].amount == 99.9
        assert result[1].active is False
        assert result[1].description == "a&amp;b"

    def test_hybrid_egress_only_native(self):
        """Test egress with only native conversions."""
        df = pl.DataFrame({
            "id": ["1", "2"],
            "amount": ["42.5", "99.9"],
            "active": ["true", "false"],
            "description": ["test1", "test2"]
        })

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "amount": {"cast": "number"}  # Native float conversion
        })

        # factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            UserDataclass,
            schema_config=config,
            auto_derive_schema=False,
            apply_defaults=False
        )

        # Native conversions applied
        assert result[0].id == 1
        assert isinstance(result[0].amount, float)
        assert result[0].amount == 42.5

    def test_hybrid_egress_only_custom(self):
        """Test egress with only custom conversions."""
        df = pl.DataFrame({
            "id": [1, 2],
            "amount": ["42.5", "99.9"],
            "active": ["yes", "no"],
            "description": ["test1", "test2"]
        })

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        # Debug: Check separation
        python_only, narwhals, native = config.separate_conversions()
        print(f"\nDEBUG: Python-only custom conversions: {python_only}")
        print(f"DEBUG: Narwhals custom conversions: {narwhals}")
        print(f"DEBUG: Native conversions: {native}")

        # factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            UserDataclass,
            schema_config=config,
            auto_derive_schema=False,
            apply_defaults=False
        )

        # Debug output
        print(f"DEBUG: Result[0].amount = {result[0].amount} (type: {type(result[0].amount)})")
        print(f"DEBUG: Result[0].active = {result[0].active} (type: {type(result[0].active)})")

        # Custom conversions applied
        assert result[0].amount == 42.5
        assert result[0].active is True
        assert result[1].amount == 99.9
        assert result[1].active is False

    def test_hybrid_egress_with_none_values(self):
        """Test hybrid egress with None values."""
        @dataclass
        class TestData:
            amount: Optional[float]
            active: Optional[bool]

        df = pl.DataFrame({
            "amount": [None, "42.5"],
            "active": [None, "yes"]
        })

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        # factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # None values preserved
        assert result[0].amount is None
        assert result[0].active is None

        # Non-None values converted
        assert result[1].amount == 42.5
        assert result[1].active is True

    def test_hybrid_egress_with_nan_values(self):
        """Test hybrid egress with NaN values using safe_float."""
        @dataclass
        class TestData:
            amount: Optional[float]

        df = pl.DataFrame({
            "amount": [float('nan'), 42.5]
        })

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"}
        })

        # factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # NaN converted to None by safe_float
        assert result[0].amount is None
        assert result[1].amount == 42.5


class TestHybridEgressMixedOperations:
    """Test hybrid egress with mixed operations (cast, rename)."""

    def test_hybrid_egress_with_rename(self):
        """Test hybrid egress with column renaming."""
        @dataclass
        class TestData:
            amount: float
            user_id: int

        df = pl.DataFrame({
            "total_amount": ["42.5", "99.9"],
            "id": ["1", "2"]
        })

        config = SchemaConfig(columns={
            "total_amount": {"cast": "safe_float", "rename": "amount"},
            "id": {"cast": "integer", "rename": "user_id"}
        })

        # factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            TestData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Conversions and renames applied
        assert result[0].amount == 42.5
        assert result[0].user_id == 1


class TestHybridEgressHelpers:
    """Test egress helper functions directly."""

    def test_apply_native_conversions_for_egress(self):
        """Test that only native conversions are applied in DataFrame."""
        from mountainash.dataframes.cast.egress_helpers import apply_native_conversions_for_egress

        df = pl.DataFrame({
            "id": ["1", "2"],
            "amount": ["42.5", "99.9"],
            "active": ["yes", "no"]
        })

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native
            "amount": {"cast": "safe_float"},    # Custom - should NOT be applied here
            "active": {"cast": "rich_boolean"}   # Custom - should NOT be applied here
        })

        result_df = apply_native_conversions_for_egress(df, config)

        # Only native conversion applied
        assert result_df["id"].dtype.base_type().is_integer()
        assert result_df["id"][0] == 1

        # Custom conversions NOT applied yet (still strings)
        assert result_df["amount"][0] == "42.5"
        assert result_df["active"][0] == "yes"

    def test_apply_custom_converters_to_namedtuples(self):
        """Test applying custom converters to named tuples."""
        from mountainash.dataframes.cast.egress_helpers import apply_custom_converters_to_python_data
        from collections import namedtuple

        # Create named tuples
        Row = namedtuple('Row', ['id', 'amount', 'active'])
        data = [
            Row(id=1, amount="42.5", active="yes"),
            Row(id=2, amount="99.9", active="no")
        ]

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        result = apply_custom_converters_to_python_data(data, config, data_format="namedtuple")

        # Custom conversions applied
        assert result[0].id == 1  # Unchanged
        assert result[0].amount == 42.5  # Converted
        assert result[0].active is True  # Converted
        assert result[1].amount == 99.9
        assert result[1].active is False


class TestHybridEgressPerformance:
    """Test performance characteristics of hybrid egress."""

    def test_large_dataset_egress(self):
        """Test hybrid egress with larger dataset."""
        @dataclass
        class LargeData:
            id: int
            amount: float
            active: bool

        # Create larger dataset
        n_rows = 1000
        df = pl.DataFrame({
            "id": [str(i) for i in range(n_rows)],
            "amount": [str(float(i) * 1.5) for i in range(n_rows)],
            "active": ["yes" if i % 2 == 0 else "no" for i in range(n_rows)]
        })

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native (vectorized, FAST!)
            "amount": {"cast": "safe_float"},    # Custom (after extraction)
            "active": {"cast": "rich_boolean"}   # Custom (after extraction)
        })

        # factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            LargeData,
            schema_config=config,
            auto_derive_schema=False
        )

        # Verify all conversions applied correctly
        assert len(result) == n_rows
        assert all(isinstance(r.id, int) for r in result)
        assert all(isinstance(r.amount, float) for r in result)
        assert all(isinstance(r.active, bool) for r in result)

        # Spot check some values
        assert result[0].id == 0
        assert result[0].amount == 0.0
        assert result[0].active is True

        assert result[999].id == 999
        assert result[999].amount == 1498.5
        assert result[999].active is False


class TestRoundTripHybrid:
    """Test complete round-trip: Python → DataFrame (ingress) → Python (egress)."""

    def test_roundtrip_with_custom_types(self):
        """Test that custom types survive a round-trip."""
        from mountainash.dataframes.ingress import PydataConverter

        @dataclass
        class RoundTripData:
            id: int
            amount: float
            active: bool
            description: str

        # Original data
        original_data = [
            {"id": "1", "amount": "42.5", "active": "yes", "description": "<tag>value</tag>"},
            {"id": "2", "amount": "99.9", "active": "no", "description": "a&b"}
        ]

        # Config with custom and native types
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"},
            "description": {"cast": "xml_string"}
        })

        # INGRESS: Python → DataFrame (hybrid strategy)
        df = PydataConverter.convert(original_data, column_config=config)

        # Verify DataFrame has correct types
        assert df["id"].dtype.base_type().is_integer()

        # EGRESS: DataFrame → Python (hybrid strategy)
        # factory = DataFrameCastFactory()
        strategy = DataFrameCastFactory.get_strategy(df)

        result = strategy._to_list_of_dataclasses(
            df,
            RoundTripData,
            schema_config=None,  # No additional transforms needed
            auto_derive_schema=False
        )

        # Verify round-trip preserved conversions
        assert result[0].id == 1
        assert result[0].amount == 42.5
        assert result[0].active is True
        assert result[0].description == "&lt;tag&gt;value&lt;/tag&gt;"

        assert result[1].id == 2
        assert result[1].amount == 99.9
        assert result[1].active is False
        assert result[1].description == "a&amp;b"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
