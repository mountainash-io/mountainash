"""Shared test fixtures and configuration for mountainash-data tests."""

import tempfile
import pytest
import sqlite3
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock
import polars as pl
import pandas as pd
import pyarrow as pa

# Import enhanced fixtures from the fixtures package
# Import using absolute path to avoid relative import issues
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fixtures'))

from mountainash.dataframes import DataFrameUtils


try:
    from fixtures.realistic_data_fixtures import (
        financial_transactions_data,
        ecommerce_orders_data,
        geographic_data,
        audit_trail_data
    )
    from fixtures.edge_case_fixtures import (
        numeric_boundary_data,
        string_boundary_data,
        datetime_boundary_data,
        null_and_missing_data
    )
    from fixtures.data_type_fixtures import (
        comprehensive_data_types,
        temporal_data_comprehensive,
        data_type_factory,
        mixed_type_scenarios
    )

except ImportError as e:
    print(f"Warning: Could not import enhanced fixtures: {e}")
    # Define placeholder fixtures to avoid import errors
    @pytest.fixture
    def financial_transactions_data():
        return {"transaction_id": [1, 2, 3], "amount": [100, 200, 300]}

    @pytest.fixture
    def numeric_boundary_data():
        return {"integers": [0, 1, -1]}

    @pytest.fixture
    def comprehensive_data_types():
        return {"strings": ["test"], "integers": [1, 2, 3]}

    @pytest.fixture
    def large_dataset_configs():
        return {"small": {"rows": 100, "cols": 5}}


@pytest.fixture(scope="session")
def temp_sqlite_db() -> Generator[Path, None, None]:
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = Path(tmp_file.name)

    # Create test tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT INTO test_table (id, name, value) VALUES
        (1, 'Alice', 100.5),
        (2, 'Bob', 200.7),
        (3, 'Charlie', 300.9)
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="session")
def sample_data_dict() -> Dict[str, Any]:
    """Provide consistent test data as dictionary."""
    return {
        "valid_simple": {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [100.5, 200.7, 300.9]
        },
        "valid_complex": {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "category": ["A", "B", "A", "C", "B"],
            "value": [100.5, 200.7, 300.9, 400.2, 500.8],
            "active": [True, False, True, True, False]
        },
        "empty": {},
        "single_column": {"id": [1, 2, 3]},
        "mixed_types": {
            "text": ["hello", "world", "test"],
            "numbers": [1, 2, 3],
            "floats": [1.1, 2.2, 3.3],
            "bools": [True, False, True]
        }
    }


@pytest.fixture(scope="session")
def sample_data_list() -> list:
    """Provide consistent test data as list of dictionaries."""
    return [
        {"id": 1, "name": "Alice", "value": 100.5, "active": True},
        {"id": 2, "name": "Bob", "value": 200.7, "active": False},
        {"id": 3, "name": "Charlie", "value": 300.9, "active": True}
    ]


@pytest.fixture
def sample_polars_df() -> pl.DataFrame:
    """Create a sample Polars DataFrame for testing."""
    return pl.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "active": [True, False, True, True, False]
    })


@pytest.fixture
def sample_pandas_df() -> pd.DataFrame:
    """Create a sample pandas DataFrame for testing."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "active": [True, False, True, True, False]
    })


@pytest.fixture
def sample_pyarrow_table() -> pa.Table:
    """Create a sample PyArrow Table for testing."""
    return pa.table({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "active": [True, False, True, True, False]
    })


@pytest.fixture
def sample_ibis_table(real_ibis_backend):
    """Create a real Ibis table using DuckDB in-memory backend."""
    # Create table from the sample data
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "active": [True, False, True, True, False]
    }

    ibis_table = DataFrameUtils.create_ibis(data)  # Ensure table exists

    # Create a real Ibis table
    # ibis_table = real_ibis_backend.create_table("test_table", data, overwrite=True)
    return ibis_table



@pytest.fixture
def column_mapping_config() -> Dict[str, str]:
    """Provide sample column mapping configuration."""
    return {
        "id": "identifier",
        "name": "full_name",
        "value": "amount",
        "active": "is_active"
    }


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Create and provide path to test data directory."""
    test_dir = Path(__file__).parent / "fixtures"
    test_dir.mkdir(exist_ok=True)
    return test_dir


# Real Ibis fixtures for more robust testing
@pytest.fixture(scope="session")
def real_ibis_backend():
    """Create a real DuckDB in-memory Ibis backend for testing."""
    import ibis
    ibis.set_backend("polars")
    return ibis.polars.connect()


@pytest.fixture
def real_ibis_table(real_ibis_backend):
    """Create a real Ibis table using DuckDB in-memory backend."""
    # Create table from the sample data
    data = {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "active": [True, False, True, True, False]
    }

    ibis_table = DataFrameUtils.create_ibis(data)  # Ensure table exists

    # Create a real Ibis table
    # ibis_table = real_ibis_backend.create_table("test_table", data, overwrite=True)
    return ibis_table


@pytest.fixture
def real_ibis_table_simple(real_ibis_backend):
    """Create a simple real Ibis table for basic tests."""
    data = {
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "value": [100.5, 200.7, 300.9],
        "active": [True, False, True]
    }

    ibis_table = DataFrameUtils.create_ibis(data)  # Ensure table exists


    # ibis_table = real_ibis_backend.create_table("test_table_simple", data, overwrite=True)
    return ibis_table


# # Mock fixtures for cases where we need to test error conditions or specific mock behaviors
# @pytest.fixture
# def mock_ibis_table():
#     """Create a properly configured mock Ibis table - use only when real table won't work."""
#     mock_table = Mock()
#     mock_table.columns = ["id", "name", "value", "active"]
#     mock_table.schema.return_value = Mock()
#     mock_table.count.return_value = Mock()
#     mock_table.count.return_value.execute.return_value = 3
#     mock_table.to_polars.return_value = pl.DataFrame({
#         "id": [1, 2, 3],
#         "name": ["Alice", "Bob", "Charlie"],
#         "value": [100.5, 200.7, 300.9],
#         "active": [True, False, True]
#     })
#     mock_table.to_pandas.return_value = pd.DataFrame({
#         "id": [1, 2, 3],
#         "name": ["Alice", "Bob", "Charlie"],
#         "value": [100.5, 200.7, 300.9],
#         "active": [True, False, True]
#     })
#     mock_table.to_pyarrow.return_value = pa.table({
#         "id": [1, 2, 3],
#         "name": ["Alice", "Bob", "Charlie"],
#         "value": [100.5, 200.7, 300.9],
#         "active": [True, False, True]
#     })
#     return mock_table


# @pytest.fixture
# def mock_ibis_backend():
#     """Create a properly configured mock Ibis backend - use only when real backend won't work."""
#     mock_backend = Mock()
#     mock_backend.create_table.return_value = Mock()
#     mock_backend.create_table.return_value.columns = ["id", "name", "value", "active"]
#     return mock_backend


# @pytest.fixture
# def mock_database_settings():
#     """Create mock database settings."""
#     mock_settings = Mock()
#     mock_settings.database_path = ":memory:"
#     mock_settings.connection_string = "sqlite:///:memory:"
#     return mock_settings
