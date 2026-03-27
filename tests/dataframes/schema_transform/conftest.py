"""
Shared fixtures for schema_transform tests.

Provides test data as Python dicts and factory functions to convert
to various DataFrame backends for parameterized testing.
"""
import pytest
from typing import Dict, Any, List


# ============================================================================
# Test Data Fixtures (Pure Python Dicts)
# ============================================================================

@pytest.fixture
def missing_values_simple_data() -> Dict[str, List[str]]:
    """Simple data with empty strings to test default missing_values."""
    return {
        "name": ["Alice", "", "Bob"],
        "score": ["95", "", "87"]
    }


@pytest.fixture
def missing_values_custom_markers_data() -> Dict[str, List[str]]:
    """Data with various missing value markers (NA, N/A, null, -)."""
    return {
        "value1": ["10", "NA", "20"],
        "value2": ["30", "N/A", "40"],
        "value3": ["50", "null", "60"],
        "value4": ["70", "-", "80"]
    }


@pytest.fixture
def boolean_values_basic_data() -> Dict[str, List[str]]:
    """Simple yes/no boolean data."""
    return {
        "approved": ["yes", "no", "yes", "no"]
    }


@pytest.fixture
def boolean_values_multiple_representations_data() -> Dict[str, List[str]]:
    """Multiple representations of true/false."""
    return {
        "flag": ["yes", "Y", "true", "1", "no", "N", "false", "0"]
    }


@pytest.fixture
def boolean_values_unmapped_data() -> Dict[str, List[str]]:
    """Boolean data with unmapped values."""
    return {
        "status": ["yes", "no", "maybe", "unknown"]
    }


@pytest.fixture
def combined_features_data() -> Dict[str, List[str]]:
    """Data combining missing_values and boolean conversion."""
    return {
        "approved": ["yes", "NA", "no", "N/A", "yes"]
    }


@pytest.fixture
def comprehensive_pipeline_data() -> Dict[str, List[str]]:
    """Comprehensive data testing all features together."""
    return {
        "id": ["1", "2", "NA", "4"],
        "approved": ["yes", "no", "null", "Y"],
        "score": ["95", "-", "87", "N/A"],
        "name": ["Alice", "Bob", "Charlie", ""]
    }


@pytest.fixture
def rename_simple_data() -> Dict[str, List[str]]:
    """Simple data for testing column renaming."""
    return {
        "user_id": ["1", "2", "3"],
        "user_name": ["Alice", "Bob", "Charlie"],
        "user_age": ["25", "30", "35"]
    }


@pytest.fixture
def default_values_data() -> Dict[str, List[str]]:
    """Data with some columns for testing default values on missing columns."""
    return {
        "id": ["1", "2", "3"],
        "name": ["Alice", "Bob", "Charlie"]
        # Missing: status, created_at columns (to be added with defaults)
    }


@pytest.fixture
def keep_only_mapped_data() -> Dict[str, List[str]]:
    """Data with extra columns for testing keep_only_mapped."""
    return {
        "id": ["1", "2", "3"],
        "name": ["Alice", "Bob", "Charlie"],
        "extra1": ["x", "y", "z"],
        "extra2": ["a", "b", "c"]
    }


@pytest.fixture
def strict_mode_data() -> Dict[str, List[str]]:
    """Data for testing strict mode error handling."""
    return {
        "id": ["1", "2", "3"],
        "name": ["Alice", "Bob", "Charlie"]
        # Missing: required_field (for strict mode test)
    }


# ============================================================================
# DataFrame Creation Factory
# ============================================================================

@pytest.fixture
def create_dataframe():
    """
    Factory function to create DataFrames from Python dicts.

    Returns a function that takes (data_dict, backend) and returns
    a DataFrame of the appropriate backend type.
    """
    def _create(data: Dict[str, List[Any]], backend: str):
        """
        Create DataFrame from dict for specified backend.

        Args:
            data: Dict mapping column names to lists of values
            backend: One of "polars", "pandas", "narwhals", "ibis", "pyarrow"

        Returns:
            DataFrame of the specified backend type
        """
        if backend == "polars":
            import polars as pl
            return pl.DataFrame(data)

        elif backend == "pandas":
            import pandas as pd
            return pd.DataFrame(data)

        elif backend == "narwhals":
            import polars as pl
            import narwhals as nw
            # Narwhals wraps another backend, use Polars underneath
            return nw.from_native(pl.DataFrame(data))

        elif backend == "ibis":
            import ibis
            import polars as pl
            # Create via Polars then convert to Ibis
            pl_df = pl.DataFrame(data)
            return ibis.memtable(pl_df)

        elif backend == "pyarrow":
            import pyarrow as pa
            return pa.table(data)

        else:
            raise ValueError(f"Unknown backend: {backend}")

    return _create


@pytest.fixture
def get_column_value():
    """
    Factory function to extract column values from any DataFrame backend.

    Returns a function that takes (df, column, index) and returns the value,
    handling backend-specific differences.
    """
    def _get_value(df, column: str, index: int):
        """
        Get value from DataFrame at column[index].

        Args:
            df: DataFrame of any backend type
            column: Column name
            index: Row index

        Returns:
            The value at df[column][index]
        """
        df_type = type(df).__module__.split('.')[0]

        if df_type == "polars":
            return df[column][index]

        elif df_type == "pandas":
            value = df[column].iloc[index]
            # Handle pandas NaN/None
            import pandas as pd
            import numpy as np
            if pd.isna(value):
                return None
            # Convert numpy types to Python types for comparison
            if isinstance(value, (np.bool_, np.generic)):
                return value.item()
            return value

        elif df_type == "narwhals":
            # Narwhals DataFrames have to_native()
            native = df.to_native()
            return native[column][index]

        elif df_type == "ibis":
            # Ibis tables need to be executed
            result = df.execute()
            value = result[column].iloc[index]
            # Handle pandas NaN/None (ibis execute() returns pandas)
            import pandas as pd
            import numpy as np
            if pd.isna(value):
                return None
            # Convert numpy types to Python types for comparison
            if isinstance(value, (np.bool_, np.generic)):
                return value.item()
            return value

        elif df_type == "pyarrow":
            # PyArrow tables
            column_data = df.column(column)
            value = column_data[index].as_py()
            return value

        else:
            raise ValueError(f"Unknown DataFrame type: {df_type}")

    return _get_value


@pytest.fixture
def get_columns():
    """
    Factory function to get column names from any DataFrame backend.

    Returns a function that takes a DataFrame and returns column names.
    """
    def _get_columns(df):
        """
        Get column names from DataFrame.

        Args:
            df: DataFrame of any backend type

        Returns:
            List of column names
        """
        df_type = type(df).__module__.split('.')[0]

        if df_type == "polars":
            return df.columns

        elif df_type == "pandas":
            return list(df.columns)

        elif df_type == "narwhals":
            return df.columns

        elif df_type == "ibis":
            return df.columns

        elif df_type == "pyarrow":
            # PyArrow uses column_names
            return df.column_names

        else:
            raise ValueError(f"Unknown DataFrame type: {df_type}")

    return _get_columns


# ============================================================================
# Backend Parameterization
# ============================================================================

# List of backends to test
# All backends now have Frictionless features implemented
IMPLEMENTED_BACKENDS = ["polars", "pandas", "narwhals", "ibis", "pyarrow"]
ALL_BACKENDS = ["polars", "pandas", "narwhals", "ibis", "pyarrow"]


def pytest_generate_tests(metafunc):
    """
    Auto-parameterize tests that request 'backend' fixture.

    Tests can use @pytest.mark.all_backends to test all backends,
    or @pytest.mark.implemented_backends to test only implemented ones.
    """
    if "backend" in metafunc.fixturenames:
        # Check for markers
        if metafunc.definition.get_closest_marker("all_backends"):
            backends = ALL_BACKENDS
        elif metafunc.definition.get_closest_marker("implemented_backends"):
            backends = IMPLEMENTED_BACKENDS
        else:
            # Default: only implemented backends
            backends = IMPLEMENTED_BACKENDS

        metafunc.parametrize("backend", backends)
