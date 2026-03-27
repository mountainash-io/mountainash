"""
Tests for Ibis with multiple in-memory backends.

This module tests Ibis cast operations with different backends (polars, duckdb, sqlite)
and ensures backend checking and compatibility functions work correctly.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.cast.cast_from_ibis import CastFromIbis
from mountainash.dataframes.cast.cast_to_ibis import CastToIbisMixin


# ============================================================================
# BACKEND FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def polars_backend():
    """Create a Polars Ibis backend."""
    # ibis.set_backend("polars")
    return ibis.polars.connect()


@pytest.fixture(scope="module")
def duckdb_backend():
    """Create a DuckDB Ibis backend."""
    # ibis.set_backend("duckdb")
    return ibis.duckdb.connect()


@pytest.fixture(scope="module")
def sqlite_backend():
    """Create a SQLite Ibis backend."""
    # ibis.set_backend("polars")
    return ibis.sqlite.connect()


@pytest.fixture
def sample_pandas_df():
    """Sample pandas DataFrame for backend tests."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8]
    })


@pytest.fixture
def ibis_table_polars(sample_pandas_df, polars_backend):
    """Ibis table using Polars backend."""
    return polars_backend.create_table("test_polars", sample_pandas_df, overwrite=True)


@pytest.fixture
def ibis_table_duckdb(sample_pandas_df, duckdb_backend):
    """Ibis table using DuckDB backend."""
    return duckdb_backend.create_table("test_duckdb", sample_pandas_df, overwrite=True)


@pytest.fixture
def ibis_table_sqlite(sample_pandas_df, sqlite_backend):
    """Ibis table using SQLite backend."""
    return sqlite_backend.create_table("test_sqlite", sample_pandas_df, overwrite=True)


# ============================================================================
# BACKEND DETECTION TESTS
# ============================================================================

@pytest.mark.unit
class TestBackendDetection:
    """Test Ibis backend detection and identification."""

    def test_get_backend_polars(self, ibis_table_polars):
        """Test getting backend from Polars Ibis table."""
        backend = CastToIbisMixin._get_ibis_backend(ibis_table_polars)

        assert backend is not None
        assert backend.name == "polars"

    def test_get_backend_duckdb(self, ibis_table_duckdb):
        """Test getting backend from DuckDB Ibis table."""
        backend = CastToIbisMixin._get_ibis_backend(ibis_table_duckdb)

        assert backend is not None
        assert backend.name == "duckdb"

    def test_get_backend_sqlite(self, ibis_table_sqlite):
        """Test getting backend from SQLite Ibis table."""
        backend = CastToIbisMixin._get_ibis_backend(ibis_table_sqlite)

        assert backend is not None
        assert backend.name == "sqlite"

    def test_get_backend_name_polars(self, ibis_table_polars):
        """Test getting backend name from Polars table."""
        name = CastToIbisMixin._get_ibis_backend_name(ibis_table_polars)

        assert name == "polars"

    def test_get_backend_name_duckdb(self, ibis_table_duckdb):
        """Test getting backend name from DuckDB table."""
        name = CastToIbisMixin._get_ibis_backend_name(ibis_table_duckdb)

        assert name == "duckdb"

    def test_get_backend_name_sqlite(self, ibis_table_sqlite):
        """Test getting backend name from SQLite table."""
        name = CastToIbisMixin._get_ibis_backend_name(ibis_table_sqlite)

        assert name == "sqlite"


@pytest.mark.unit
class TestCheckBackendsSame:
    """Test _check_ibis_backends_same() function."""

    def test_same_backend_polars_identity(self, ibis_table_polars, polars_backend):
        """Test same Polars backend using identity check."""
        result = CastToIbisMixin._check_ibis_backends_same(ibis_table_polars, polars_backend)

        # Should be True - same backend instance
        assert result is True

    def test_same_backend_duckdb_identity(self, ibis_table_duckdb, duckdb_backend):
        """Test same DuckDB backend using identity check."""
        result = CastToIbisMixin._check_ibis_backends_same(ibis_table_duckdb, duckdb_backend)

        # Should be True - same backend instance
        assert result is True

    def test_same_backend_sqlite_identity(self, ibis_table_sqlite, sqlite_backend):
        """Test same SQLite backend using identity check."""
        result = CastToIbisMixin._check_ibis_backends_same(ibis_table_sqlite, sqlite_backend)

        # Should be True - same backend instance
        assert result is True

    def test_different_backend_polars_vs_duckdb(self, ibis_table_polars, duckdb_backend):
        """Test different backends (Polars vs DuckDB)."""
        result = CastToIbisMixin._check_ibis_backends_same(ibis_table_polars, duckdb_backend)

        # Should be False - different backends
        assert result is False

    def test_different_backend_duckdb_vs_sqlite(self, ibis_table_duckdb, sqlite_backend):
        """Test different backends (DuckDB vs SQLite)."""
        result = CastToIbisMixin._check_ibis_backends_same(ibis_table_duckdb, sqlite_backend)

        # Should be False - different backends
        assert result is False

    def test_different_backend_sqlite_vs_polars(self, ibis_table_sqlite, polars_backend):
        """Test different backends (SQLite vs Polars)."""
        result = CastToIbisMixin._check_ibis_backends_same(ibis_table_sqlite, polars_backend)

        # Should be False - different backends
        assert result is False

    def test_different_polars_backend_instances(self, ibis_table_polars):
        """Test different Polars backend instances."""
        # Create a new Polars backend instance
        new_polars_backend = ibis.connect("polars://")

        result = CastToIbisMixin._check_ibis_backends_same(ibis_table_polars, new_polars_backend)

        # Should be False - different backend instances (not same object)
        assert result is False

    def test_different_duckdb_backend_instances(self, ibis_table_duckdb):
        """Test different DuckDB backend instances."""
        # Create a new DuckDB backend instance
        new_duckdb_backend = ibis.connect("duckdb://")

        result = CastToIbisMixin._check_ibis_backends_same(ibis_table_duckdb, new_duckdb_backend)

        # Should be False - different backend instances
        assert result is False


@pytest.mark.unit
class TestInitIbisConnection:
    """Test _init_ibis_connection() function."""

    def test_init_polars_backend_from_string(self):
        """Test creating Polars backend from string."""
        backend = CastToIbisMixin._init_ibis_connection("polars")

        assert backend is not None
        assert backend.name == "polars"

    def test_init_duckdb_backend_from_string(self):
        """Test creating DuckDB backend from string."""
        backend = CastToIbisMixin._init_ibis_connection("duckdb")

        assert backend is not None
        assert backend.name == "duckdb"

    def test_init_sqlite_backend_from_string(self):
        """Test creating SQLite backend from string."""
        backend = CastToIbisMixin._init_ibis_connection("sqlite")

        assert backend is not None
        assert backend.name == "sqlite"

    def test_init_default_backend(self):
        """Test creating default backend (should be polars)."""
        backend = CastToIbisMixin._init_ibis_connection(None)

        assert backend is not None
        assert backend.name == "polars"

    def test_init_from_existing_backend(self, polars_backend):
        """Test passing existing backend returns same backend."""
        backend = CastToIbisMixin._init_ibis_connection(polars_backend)

        assert backend is polars_backend

    def test_init_unsupported_backend_raises_error(self):
        """Test unsupported backend string raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported inmemory ibis schema"):
            CastToIbisMixin._init_ibis_connection("mysql")


@pytest.mark.unit
class TestMemtableDetection:
    """Test _is_memtable() and _is_remote_table() functions."""

    def test_polars_table_memtable_or_remote(self, ibis_table_polars):
        """Test Polars table is either memtable or remote table."""
        is_mem = CastToIbisMixin._is_memtable(ibis_table_polars)
        is_remote = CastToIbisMixin._is_remote_table(ibis_table_polars)

        # Should be one or the other, not both
        assert is_mem != is_remote

    def test_duckdb_table_memtable_or_remote(self, ibis_table_duckdb):
        """Test DuckDB table is either memtable or remote table."""
        is_mem = CastToIbisMixin._is_memtable(ibis_table_duckdb)
        is_remote = CastToIbisMixin._is_remote_table(ibis_table_duckdb)

        # Should be one or the other, not both
        assert is_mem != is_remote

    def test_sqlite_table_memtable_or_remote(self, ibis_table_sqlite):
        """Test SQLite table is either memtable or remote table."""
        is_mem = CastToIbisMixin._is_memtable(ibis_table_sqlite)
        is_remote = CastToIbisMixin._is_remote_table(ibis_table_sqlite)

        # Should be one or the other, not both
        assert is_mem != is_remote


# ============================================================================
# CAST OPERATIONS WITH DIFFERENT BACKENDS
# ============================================================================

@pytest.mark.unit
class TestCastFromPolarsBackend:
    """Test cast operations FROM Ibis tables using Polars backend."""

    def test_polars_backend_to_pandas(self, ibis_table_polars):
        """Test converting Polars-backed Ibis table to pandas."""
        strategy = CastFromIbis

        result = strategy.to_pandas(ibis_table_polars)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert list(result.columns) == ["id", "name", "value"]

    def test_polars_backend_to_polars(self, ibis_table_polars):
        """Test converting Polars-backed Ibis table to polars."""
        strategy = CastFromIbis

        result = strategy.to_polars(ibis_table_polars)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 5

    def test_polars_backend_to_pyarrow(self, ibis_table_polars):
        """Test converting Polars-backed Ibis table to pyarrow."""
        strategy = CastFromIbis

        result = strategy.to_pyarrow(ibis_table_polars)

        assert isinstance(result, pa.Table)
        assert len(result) == 5

    def test_polars_backend_to_dict(self, ibis_table_polars):
        """Test converting Polars-backed Ibis table to dict."""
        strategy = CastFromIbis

        result = strategy.to_dictionary_of_lists(ibis_table_polars)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"id", "name", "value"}


@pytest.mark.unit
class TestCastFromDuckDBBackend:
    """Test cast operations FROM Ibis tables using DuckDB backend."""

    def test_duckdb_backend_to_pandas(self, ibis_table_duckdb):
        """Test converting DuckDB-backed Ibis table to pandas."""
        strategy = CastFromIbis

        result = strategy.to_pandas(ibis_table_duckdb)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert set(result.columns) == {"id", "name", "value"}

    def test_duckdb_backend_to_polars(self, ibis_table_duckdb):
        """Test converting DuckDB-backed Ibis table to polars."""
        strategy = CastFromIbis

        result = strategy.to_polars(ibis_table_duckdb)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 5

    def test_duckdb_backend_to_pyarrow(self, ibis_table_duckdb):
        """Test converting DuckDB-backed Ibis table to pyarrow."""
        strategy = CastFromIbis

        result = strategy.to_pyarrow(ibis_table_duckdb)

        assert isinstance(result, pa.Table)
        assert len(result) == 5

    def test_duckdb_backend_to_dict(self, ibis_table_duckdb):
        """Test converting DuckDB-backed Ibis table to dict."""
        strategy = CastFromIbis

        result = strategy.to_dictionary_of_lists(ibis_table_duckdb)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"id", "name", "value"}


@pytest.mark.unit
class TestCastFromSQLiteBackend:
    """Test cast operations FROM Ibis tables using SQLite backend."""

    def test_sqlite_backend_to_pandas(self, ibis_table_sqlite):
        """Test converting SQLite-backed Ibis table to pandas."""
        strategy = CastFromIbis

        result = strategy.to_pandas(ibis_table_sqlite)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert set(result.columns) == {"id", "name", "value"}

    def test_sqlite_backend_to_polars(self, ibis_table_sqlite):
        """Test converting SQLite-backed Ibis table to polars."""
        strategy = CastFromIbis

        result = strategy.to_polars(ibis_table_sqlite)

        if isinstance(result, pl.LazyFrame):
            result = result.collect()

        assert isinstance(result, pl.DataFrame)
        assert len(result) == 5

    def test_sqlite_backend_to_pyarrow(self, ibis_table_sqlite):
        """Test converting SQLite-backed Ibis table to pyarrow."""
        strategy = CastFromIbis

        result = strategy.to_pyarrow(ibis_table_sqlite)

        assert isinstance(result, pa.Table)
        assert len(result) == 5

    def test_sqlite_backend_to_dict(self, ibis_table_sqlite):
        """Test converting SQLite-backed Ibis table to dict."""
        strategy = CastFromIbis

        result = strategy.to_dictionary_of_lists(ibis_table_sqlite)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"id", "name", "value"}


@pytest.mark.unit
class TestCastToIbisWithBackends:
    """Test cast operations TO Ibis with different backends."""

    def test_pandas_to_ibis_polars_backend(self, sample_pandas_df, polars_backend):
        """Test pandas to Ibis with Polars backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(sample_pandas_df)

        result = strategy.to_ibis(sample_pandas_df, ibis_backend=polars_backend)

        assert result is not None
        assert result.get_backend().name == "polars"
        assert set(result.columns) == set(sample_pandas_df.columns)

    def test_pandas_to_ibis_duckdb_backend(self, sample_pandas_df, duckdb_backend):
        """Test pandas to Ibis with DuckDB backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(sample_pandas_df)

        result = strategy.to_ibis(sample_pandas_df, ibis_backend=duckdb_backend)

        assert result is not None
        assert result.get_backend().name == "duckdb"
        assert set(result.columns) == set(sample_pandas_df.columns)

    def test_pandas_to_ibis_sqlite_backend(self, sample_pandas_df, sqlite_backend):
        """Test pandas to Ibis with SQLite backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(sample_pandas_df)

        result = strategy.to_ibis(sample_pandas_df, ibis_backend=sqlite_backend)

        assert result is not None
        assert result.get_backend().name == "sqlite"
        assert set(result.columns) == set(sample_pandas_df.columns)

    def test_polars_to_ibis_polars_backend(self, sample_pandas_df, polars_backend):
        """Test polars to Ibis with Polars backend."""
        polars_df = pl.DataFrame(sample_pandas_df)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_df)

        result = strategy.to_ibis(polars_df, ibis_backend=polars_backend)

        assert result is not None
        assert result.get_backend().name == "polars"

    def test_polars_to_ibis_duckdb_backend(self, sample_pandas_df, duckdb_backend):
        """Test polars to Ibis with DuckDB backend."""
        polars_df = pl.DataFrame(sample_pandas_df)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_df)

        result = strategy.to_ibis(polars_df, ibis_backend=duckdb_backend)

        assert result is not None
        assert result.get_backend().name == "duckdb"


@pytest.mark.unit
class TestBackendConsistency:
    """Test that all backends produce consistent results."""

    def test_all_backends_produce_same_pandas_result(self, sample_pandas_df, polars_backend, duckdb_backend, sqlite_backend):
        """Test all backends produce same pandas DataFrame."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(sample_pandas_df)

        # Create Ibis tables with different backends
        ibis_polars = strategy.to_ibis(sample_pandas_df, ibis_backend=polars_backend, tablename="test1")
        ibis_duckdb = strategy.to_ibis(sample_pandas_df, ibis_backend=duckdb_backend, tablename="test2")
        ibis_sqlite = strategy.to_ibis(sample_pandas_df, ibis_backend=sqlite_backend, tablename="test3")

        # Convert all back to pandas
        pandas_from_polars = CastFromIbis.to_pandas(ibis_polars)
        pandas_from_duckdb = CastFromIbis.to_pandas(ibis_duckdb)
        pandas_from_sqlite = CastFromIbis.to_pandas(ibis_sqlite)

        # All should have same shape and columns
        assert len(pandas_from_polars) == len(pandas_from_duckdb) == len(pandas_from_sqlite) == 5
        assert set(pandas_from_polars.columns) == set(pandas_from_duckdb.columns) == set(pandas_from_sqlite.columns)

    def test_all_backends_preserve_data_roundtrip(self, sample_pandas_df, polars_backend, duckdb_backend, sqlite_backend):
        """Test all backends preserve data in roundtrip."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(sample_pandas_df)

        backends = {
            "polars": polars_backend,
            "duckdb": duckdb_backend,
            "sqlite": sqlite_backend
        }

        for backend_name, backend in backends.items():
            # pandas -> ibis -> pandas
            ibis_table = strategy.to_ibis(sample_pandas_df, ibis_backend=backend, tablename=f"test_roundtrip_{backend_name}", overwrite=True)
            result = CastFromIbis.to_pandas(ibis_table)

            # Check data integrity
            assert len(result) == len(sample_pandas_df), f"{backend_name} roundtrip failed: row count mismatch"
            assert set(result.columns) == set(sample_pandas_df.columns), f"{backend_name} roundtrip failed: column mismatch"

            # Check that we have data
            assert len(result) > 0, f"{backend_name} roundtrip produced empty DataFrame"


@pytest.mark.unit
class TestIbisToIbisConversion:
    """Test converting Ibis tables between different backends."""

    def test_ibis_same_backend_returns_as_is(self, ibis_table_polars, polars_backend):
        """Test Ibis to Ibis with same backend returns original table."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table_polars)

        result = strategy.to_ibis(ibis_table_polars, ibis_backend=polars_backend)

        # Should return the same table when backend matches
        assert result is ibis_table_polars

    def test_ibis_polars_to_duckdb(self, ibis_table_polars, duckdb_backend):
        """Test converting Ibis table from Polars to DuckDB backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table_polars)

        result = strategy.to_ibis(ibis_table_polars, ibis_backend=duckdb_backend, tablename="converted")

        # Should create new table on DuckDB backend
        assert result is not None
        assert result.get_backend().name == "duckdb"
        assert set(result.columns) == set(ibis_table_polars.columns)

    def test_ibis_duckdb_to_sqlite(self, ibis_table_duckdb, sqlite_backend):
        """Test converting Ibis table from DuckDB to SQLite backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table_duckdb)

        result = strategy.to_ibis(ibis_table_duckdb, ibis_backend=sqlite_backend, tablename="converted")

        # Should create new table on SQLite backend
        assert result is not None
        assert result.get_backend().name == "sqlite"

    def test_ibis_sqlite_to_polars(self, ibis_table_sqlite, polars_backend):
        """Test converting Ibis table from SQLite to Polars backend."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table_sqlite)

        result = strategy.to_ibis(ibis_table_sqlite, ibis_backend=polars_backend, tablename="converted")

        # Should create new table on Polars backend
        assert result is not None
        assert result.get_backend().name == "polars"


@pytest.mark.unit
class TestBackendSpecificFeatures:
    """Test backend-specific features and capabilities."""

    def test_polars_backend_supports_operations(self, ibis_table_polars):
        """Test Polars backend supports Ibis operations."""
        # Filter operation
        filtered = ibis_table_polars.filter(ibis_table_polars['id'] > 2)

        # Materialize
        result = CastFromIbis.to_pandas(filtered)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3  # IDs 3, 4, 5

    def test_duckdb_backend_supports_operations(self, ibis_table_duckdb):
        """Test DuckDB backend supports Ibis operations."""
        # Filter operation
        filtered = ibis_table_duckdb.filter(ibis_table_duckdb['value'] > 200.0)

        # Materialize
        result = CastFromIbis.to_pandas(filtered)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert all(result['value'] > 200.0)

    def test_sqlite_backend_supports_operations(self, ibis_table_sqlite):
        """Test SQLite backend supports Ibis operations."""
        # Select operation
        selected = ibis_table_sqlite.select(['id', 'name'])

        # Materialize
        result = CastFromIbis.to_pandas(selected)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['id', 'name']


@pytest.mark.unit
class TestGenerateTablename:
    """Test _generate_tablename() function."""

    def test_generate_tablename_no_prefix(self):
        """Test generating table name without prefix."""
        name = CastToIbisMixin._generate_tablename()

        assert isinstance(name, str)
        assert len(name) > 0
        # Should be a UUID string
        assert '-' in name

    def test_generate_tablename_with_prefix(self):
        """Test generating table name with prefix."""
        name = CastToIbisMixin._generate_tablename(prefix="test_prefix")

        assert isinstance(name, str)
        assert name.startswith("test_prefix_")
        assert '-' in name  # UUID part

    def test_generate_tablename_unique(self):
        """Test that generated table names are unique."""
        name1 = CastToIbisMixin._generate_tablename()
        name2 = CastToIbisMixin._generate_tablename()

        assert name1 != name2
