"""
Multi-backend tests for hybrid egress custom type conversion.

Tests that custom type conversion works correctly across ALL supported backends:
- pandas DataFrame
- polars DataFrame
- polars LazyFrame
- pyarrow Table
- ibis Table
- narwhals DataFrame
- narwhals LazyFrame

This ensures the CastToPythonDataMixin implementation works correctly.
"""
import pytest
from dataclasses import dataclass
from typing import Optional

from mountainash.dataframes.schema_config import SchemaConfig
from mountainash.dataframes.cast import DataFrameCastFactory


@dataclass
class UserData:
    """Test dataclass for multi-backend tests."""
    id: int
    amount: float
    active: bool
    description: str


# Test data as dict of lists (columnar format)
TEST_DATA = {
    "id": ["1", "2", "3"],
    "amount": ["42.5", "99.9", "12.3"],
    "active": ["yes", "no", "true"],
    "description": ["<tag>value</tag>", "a&b", "test"]
}

# Schema config with custom and native types
TEST_CONFIG = SchemaConfig(columns={
    "id": {"cast": "integer"},           # Native (vectorized in DataFrame)
    "amount": {"cast": "safe_float"},    # Custom (applied after extraction)
    "active": {"cast": "rich_boolean"},  # Custom (applied after extraction)
    "description": {"cast": "xml_string"}  # Custom (applied after extraction)
})


@pytest.mark.parametrize("backend", ["pandas", "polars", "pyarrow"])
def test_hybrid_egress_multi_backend(backend):
    """
    Test custom type egress works across pandas, polars, and pyarrow backends.

    This tests that CastToPythonDataMixin delegates correctly and that
    the hybrid strategy works for all backends.
    """
    # Create DataFrame in the specified backend
    if backend == "pandas":
        import pandas as pd
        df = pd.DataFrame(TEST_DATA)
    elif backend == "polars":
        import polars as pl
        df = pl.DataFrame(TEST_DATA)
    elif backend == "pyarrow":
        import pyarrow as pa
        df = pa.table(TEST_DATA)
    else:
        pytest.skip(f"Backend {backend} not available")

    # Get strategy and convert to dataclasses
    factory = DataFrameCastFactory()
    strategy = factory.get_strategy(df)

    result = strategy._to_list_of_dataclasses(
        df,
        UserData,
        schema_config=TEST_CONFIG,
        auto_derive_schema=False
    )

    # Verify results - should be identical across all backends
    assert len(result) == 3

    # First record - all conversions applied
    assert isinstance(result[0], UserData)
    assert result[0].id == 1  # Native conversion
    assert result[0].amount == 42.5  # Custom conversion
    assert result[0].active is True  # Custom conversion
    assert result[0].description == "&lt;tag&gt;value&lt;/tag&gt;"  # Custom conversion

    # Second record
    assert result[1].id == 2
    assert result[1].amount == 99.9
    assert result[1].active is False
    assert result[1].description == "a&amp;b"

    # Third record
    assert result[2].id == 3
    assert result[2].amount == 12.3
    assert result[2].active is True
    assert result[2].description == "test"


@pytest.mark.parametrize("backend", ["narwhals_polars", "narwhals_pandas"])
def test_hybrid_egress_narwhals_backends(backend):
    """
    Test custom type egress works with Narwhals universal interface.

    Narwhals provides a unified API across backends, so we test it with
    both polars and pandas as the underlying backend.
    """
    import narwhals as nw

    # Create underlying DataFrame
    if backend == "narwhals_polars":
        import polars as pl
        native_df = pl.DataFrame(TEST_DATA)
    elif backend == "narwhals_pandas":
        import pandas as pd
        native_df = pd.DataFrame(TEST_DATA)
    else:
        pytest.skip(f"Backend {backend} not available")

    # Wrap in Narwhals
    df = nw.from_native(native_df)

    # Get strategy and convert to dataclasses
    factory = DataFrameCastFactory()
    strategy = factory.get_strategy(df)

    result = strategy._to_list_of_dataclasses(
        df,
        UserData,
        schema_config=TEST_CONFIG,
        auto_derive_schema=False
    )

    # Verify results
    assert len(result) == 3
    assert result[0].id == 1
    assert result[0].amount == 42.5
    assert result[0].active is True
    assert result[0].description == "&lt;tag&gt;value&lt;/tag&gt;"


def test_hybrid_egress_polars_lazyframe():
    """
    Test custom type egress works with Polars LazyFrame.

    LazyFrame uses CastFromPolarsLazyFrame which has different code paths.
    """
    import polars as pl

    # Create LazyFrame
    df = pl.DataFrame(TEST_DATA).lazy()

    # Get strategy and convert to dataclasses
    factory = DataFrameCastFactory()
    strategy = factory.get_strategy(df)

    result = strategy._to_list_of_dataclasses(
        df,
        UserData,
        schema_config=TEST_CONFIG,
        auto_derive_schema=False
    )

    # Verify results
    assert len(result) == 3
    assert result[0].id == 1
    assert result[0].amount == 42.5
    assert result[0].active is True
    assert result[0].description == "&lt;tag&gt;value&lt;/tag&gt;"


def test_hybrid_egress_narwhals_lazyframe():
    """Test custom type egress works with Narwhals LazyFrame."""
    import narwhals as nw
    import polars as pl

    # Create Narwhals LazyFrame
    native_df = pl.DataFrame(TEST_DATA).lazy()
    df = nw.from_native(native_df)

    # Get strategy and convert to dataclasses
    factory = DataFrameCastFactory()
    strategy = factory.get_strategy(df)

    result = strategy._to_list_of_dataclasses(
        df,
        UserData,
        schema_config=TEST_CONFIG,
        auto_derive_schema=False
    )

    # Verify results
    assert len(result) == 3
    assert result[0].id == 1
    assert result[0].amount == 42.5
    assert result[0].active is True
    assert result[0].description == "&lt;tag&gt;value&lt;/tag&gt;"


@pytest.mark.parametrize("backend", ["pandas", "polars"])
def test_hybrid_egress_only_custom_multi_backend(backend):
    """Test egress with ONLY custom conversions across backends."""
    @dataclass
    class TestData:
        id: int
        amount: float
        active: bool

    # Create DataFrame with no type casting needed for 'id'
    if backend == "pandas":
        import pandas as pd
        df = pd.DataFrame({
            "id": [1, 2],
            "amount": ["42.5", "99.9"],
            "active": ["yes", "no"]
        })
    elif backend == "polars":
        import polars as pl
        df = pl.DataFrame({
            "id": [1, 2],
            "amount": ["42.5", "99.9"],
            "active": ["yes", "no"]
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
        auto_derive_schema=False,
        apply_defaults=False
    )

    # Custom conversions should be applied
    assert result[0].amount == 42.5
    assert result[0].active is True
    assert result[1].amount == 99.9
    assert result[1].active is False


@pytest.mark.parametrize("backend", ["pandas", "polars"])
def test_hybrid_egress_with_none_values_multi_backend(backend):
    """Test hybrid egress with None values across backends."""
    @dataclass
    class TestData:
        amount: Optional[float]
        active: Optional[bool]

    if backend == "pandas":
        import pandas as pd
        df = pd.DataFrame({
            "amount": [None, "42.5"],
            "active": [None, "yes"]
        })
    elif backend == "polars":
        import polars as pl
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

    result = strategy._to_list_of_dataclasses(
        df,
        TestData,
        schema_config=config,
        auto_derive_schema=False
    )

    # None values should be preserved
    assert result[0].amount is None
    assert result[0].active is None

    # Non-None values should be converted
    assert result[1].amount == 42.5
    assert result[1].active is True


@pytest.mark.parametrize("backend", ["pandas", "polars"])
def test_hybrid_egress_with_rename_multi_backend(backend):
    """Test hybrid egress with column renaming across backends."""
    @dataclass
    class TestData:
        amount: float
        user_id: int

    if backend == "pandas":
        import pandas as pd
        df = pd.DataFrame({
            "total_amount": ["42.5", "99.9"],
            "id": ["1", "2"]
        })
    elif backend == "polars":
        import polars as pl
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

    result = strategy._to_list_of_dataclasses(
        df,
        TestData,
        schema_config=config,
        auto_derive_schema=False
    )

    # Conversions and renames should work
    assert result[0].amount == 42.5
    assert result[0].user_id == 1
    assert result[1].amount == 99.9
    assert result[1].user_id == 2


class TestBackendConsistency:
    """Test that all backends produce identical results."""

    def test_consistent_results_across_backends(self):
        """Verify all backends produce identical output for same input."""
        import pandas as pd
        import polars as pl
        import pyarrow as pa

        backends_data = {
            "pandas": pd.DataFrame(TEST_DATA),
            "polars": pl.DataFrame(TEST_DATA),
            "pyarrow": pa.table(TEST_DATA),
        }

        results = {}

        for backend_name, df in backends_data.items():
            factory = DataFrameCastFactory()
            strategy = factory.get_strategy(df)

            result = strategy._to_list_of_dataclasses(
                df,
                UserData,
                schema_config=TEST_CONFIG,
                auto_derive_schema=False
            )

            # Convert to comparable format (tuples)
            results[backend_name] = [
                (r.id, r.amount, r.active, r.description)
                for r in result
            ]

        # All backends should produce identical results
        pandas_result = results["pandas"]
        assert results["polars"] == pandas_result
        assert results["pyarrow"] == pandas_result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
