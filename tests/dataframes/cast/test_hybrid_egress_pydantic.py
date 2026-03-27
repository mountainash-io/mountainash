"""
Pydantic model tests for hybrid egress custom type conversion.

Tests that custom type conversion works correctly when converting
DataFrames to Pydantic models (BaseModel).
"""
import pytest
from typing import Optional

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

import polars as pl
from mountainash.dataframes.schema_config import SchemaConfig
from mountainash.dataframes.cast import DataFrameCastFactory


pytestmark = pytest.mark.skipif(
    not PYDANTIC_AVAILABLE,
    reason="pydantic not installed"
)


class UserModel(BaseModel):
    """Test Pydantic model for egress tests."""
    id: int
    amount: float
    active: bool
    description: str


class TestHybridEgressPydantic:
    """Test hybrid egress conversion to Pydantic models."""

    def test_hybrid_egress_pydantic_custom_and_native(self):
        """Test that custom and native conversions work with Pydantic models."""
        # Create test DataFrame
        df = pl.DataFrame({
            "id": ["1", "2", "3"],
            "amount": ["42.5", "99.9", "12.3"],
            "active": ["yes", "no", "true"],
            "description": ["<tag>value</tag>", "a&b", "test"]
        })

        # Config with both custom and native conversions
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},           # Native (vectorized in DF)
            "amount": {"cast": "safe_float"},    # Custom (after extraction)
            "active": {"cast": "rich_boolean"},  # Custom (after extraction)
            "description": {"cast": "xml_string"}  # Custom (after extraction)
        })

        # Convert using hybrid egress strategy
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            UserModel,
            schema_config=config,
            auto_derive_schema=False
        )

        # Verify results
        assert len(result) == 3

        # Check first record
        assert isinstance(result[0], UserModel)
        assert result[0].id == 1  # Native conversion
        assert result[0].amount == 42.5  # Custom conversion
        assert result[0].active is True  # Custom conversion
        assert result[0].description == "&lt;tag&gt;value&lt;/tag&gt;"  # Custom conversion

        # Check second record
        assert result[1].id == 2
        assert result[1].amount == 99.9
        assert result[1].active is False
        assert result[1].description == "a&amp;b"

    def test_hybrid_egress_pydantic_only_native(self):
        """Test Pydantic egress with only native conversions."""
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

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            UserModel,
            schema_config=config,
            auto_derive_schema=False
        )

        # Native conversions applied
        assert result[0].id == 1
        assert isinstance(result[0].amount, float)
        assert result[0].amount == 42.5

    def test_hybrid_egress_pydantic_only_custom(self):
        """Test Pydantic egress with only custom conversions."""
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

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            UserModel,
            schema_config=config,
            auto_derive_schema=False
        )

        # Custom conversions applied
        assert result[0].amount == 42.5
        assert result[0].active is True
        assert result[1].amount == 99.9
        assert result[1].active is False

    def test_hybrid_egress_pydantic_with_none_values(self):
        """Test Pydantic egress with None values."""
        class TestModel(BaseModel):
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

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            TestModel,
            schema_config=config,
            auto_derive_schema=False
        )

        # None values preserved
        assert result[0].amount is None
        assert result[0].active is None

        # Non-None values converted
        assert result[1].amount == 42.5
        assert result[1].active is True

    def test_hybrid_egress_pydantic_with_nan_values(self):
        """Test Pydantic egress with NaN values using safe_float."""
        class TestModel(BaseModel):
            amount: Optional[float]

        df = pl.DataFrame({
            "amount": [float('nan'), 42.5]
        })

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            TestModel,
            schema_config=config,
            auto_derive_schema=False
        )

        # NaN converted to None by safe_float
        assert result[0].amount is None
        assert result[1].amount == 42.5

    def test_hybrid_egress_pydantic_with_rename(self):
        """Test Pydantic egress with column renaming."""
        class TestModel(BaseModel):
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

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            TestModel,
            schema_config=config,
            auto_derive_schema=False
        )

        # Conversions and renames applied
        assert result[0].amount == 42.5
        assert result[0].user_id == 1

    def test_hybrid_egress_pydantic_with_field_validator(self):
        """Test that Pydantic validators work after custom conversions."""
        from pydantic import field_validator

        class ValidatedModel(BaseModel):
            amount: float
            active: bool

            @field_validator('amount')
            @classmethod
            def amount_must_be_positive(cls, v):
                if v < 0:
                    raise ValueError('amount must be positive')
                return v

        df = pl.DataFrame({
            "amount": ["42.5", "99.9"],
            "active": ["yes", "no"]
        })

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            ValidatedModel,
            schema_config=config,
            auto_derive_schema=False
        )

        # Custom conversions applied, then Pydantic validation
        assert result[0].amount == 42.5
        assert result[0].active is True

    def test_hybrid_egress_pydantic_validation_failure(self):
        """Test that Pydantic validation failures are handled properly."""
        from pydantic import field_validator, ValidationError

        class StrictModel(BaseModel):
            amount: float

            @field_validator('amount')
            @classmethod
            def amount_must_be_positive(cls, v):
                if v < 0:
                    raise ValueError('amount must be positive')
                return v

        df = pl.DataFrame({
            "amount": ["-10.5", "99.9"]  # First value is negative
        })

        config = SchemaConfig(columns={
            "amount": {"cast": "safe_float"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        # Should raise ValidationError on first record
        with pytest.raises(ValidationError):
            strategy._to_list_of_pydantic(
                df,
                StrictModel,
                schema_config=config,
                auto_derive_schema=False
            )


class TestHybridEgressPydanticMultiBackend:
    """Test Pydantic egress across different DataFrame backends."""

    @pytest.mark.parametrize("backend", ["pandas", "polars", "pyarrow"])
    def test_pydantic_egress_multi_backend(self, backend):
        """Test Pydantic conversion works across all backends."""
        # Create DataFrame in specified backend
        if backend == "pandas":
            import pandas as pd
            df = pd.DataFrame({
                "id": ["1", "2"],
                "amount": ["42.5", "99.9"],
                "active": ["yes", "no"],
                "description": ["test1", "test2"]
            })
        elif backend == "polars":
            df = pl.DataFrame({
                "id": ["1", "2"],
                "amount": ["42.5", "99.9"],
                "active": ["yes", "no"],
                "description": ["test1", "test2"]
            })
        elif backend == "pyarrow":
            import pyarrow as pa
            df = pa.table({
                "id": ["1", "2"],
                "amount": ["42.5", "99.9"],
                "active": ["yes", "no"],
                "description": ["test1", "test2"]
            })

        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "amount": {"cast": "safe_float"},
            "active": {"cast": "rich_boolean"}
        })

        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            UserModel,
            schema_config=config,
            auto_derive_schema=False
        )

        # Verify conversions work across all backends
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].amount == 42.5
        assert result[0].active is True


class TestRoundTripPydantic:
    """Test complete round-trip with Pydantic models."""

    def test_roundtrip_pydantic_with_custom_types(self):
        """Test that custom types survive a round-trip with Pydantic."""
        from mountainash.dataframes.ingress import PydataConverter

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

        # EGRESS: DataFrame → Pydantic (hybrid strategy)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(df)

        result = strategy._to_list_of_pydantic(
            df,
            UserModel,
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
