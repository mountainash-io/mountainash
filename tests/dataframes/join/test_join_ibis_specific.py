"""
Tests for Ibis-specific join features.

This module tests Ibis-specific functionality like execute_on parameter,
backend resolution, and cross-backend DataFrame joins.
"""

import pytest
import pandas as pd
import polars as pl
import ibis

from mountainash.dataframes.join.join_ibis import IbisJoinStrategy
from mountainash.dataframes.join import DataFrameJoinFactory
from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.cast import DataFrameCastFactory


@pytest.mark.unit
class TestIbisBackendResolution:
    """Test Ibis backend detection and resolution."""

    def test_get_ibis_backend(self, left_ibis_table):
        """Test extracting backend from Ibis table."""
        backend = IbisJoinStrategy._get_ibis_backend(left_ibis_table)

        assert backend is not None
        assert hasattr(backend, 'name')
        # Should be one of the in-memory backends
        assert backend.name in ["polars", "duckdb", "sqlite"]

    def test_get_ibis_backend_name(self, left_ibis_table):
        """Test extracting backend name from Ibis table."""
        # Use class methods directly
        backend_name = IbisJoinStrategy._get_ibis_backend_name(left_ibis_table)

        assert backend_name in ["polars", "duckdb", "sqlite"]

    def test_check_backends_same(self, left_ibis_table, right_ibis_table):
        """Test checking if two Ibis backends are the same."""
        # Use class methods directly

        left_backend = IbisJoinStrategy._get_ibis_backend(left_ibis_table)
        right_backend = IbisJoinStrategy._get_ibis_backend(right_ibis_table)

        # Both created from same fixture should have same backend
        are_same = IbisJoinStrategy._check_backends_same(left_backend, right_backend)
        assert are_same

    def test_init_ibis_connection_default(self):
        """Test initializing Ibis connection with defaults."""
        # Use class methods directly
        backend = IbisJoinStrategy._init_ibis_connection()

        assert backend is not None
        assert backend.name == "polars"  # Default

    def test_init_ibis_connection_duckdb(self):
        """Test initializing Ibis connection with DuckDB."""
        # Use class methods directly
        backend = IbisJoinStrategy._init_ibis_connection("duckdb")

        assert backend is not None
        assert backend.name == "duckdb"

    def test_init_ibis_connection_sqlite(self):
        """Test initializing Ibis connection with SQLite."""
        # Use class methods directly
        backend = IbisJoinStrategy._init_ibis_connection("sqlite")

        assert backend is not None
        assert backend.name == "sqlite"

    def test_init_ibis_connection_invalid(self):
        """Test that invalid backend raises error."""
        # Use class methods directly

        with pytest.raises(TypeError):
            IbisJoinStrategy._init_ibis_connection("invalid_backend")


@pytest.mark.unit
class TestIbisTableResolution:
    """Test Ibis table resolution from various DataFrame types."""

    def test_resolve_pandas_to_ibis(self, left_pandas_df):
        """Test resolving pandas DataFrame to Ibis table."""
        # Use class methods directly
        ibis_table = IbisJoinStrategy._resolve_ibis_table(left_pandas_df)

        assert isinstance(ibis_table, ibis.expr.types.Table)
        # Table should be in-memory (memtable)
        assert ibis_table is not None

    def test_resolve_polars_to_ibis(self, left_polars_df):
        """Test resolving Polars DataFrame to Ibis table."""
        # Use class methods directly
        ibis_table = IbisJoinStrategy._resolve_ibis_table(left_polars_df)

        assert isinstance(ibis_table, ibis.expr.types.Table)

    def test_resolve_ibis_table_passthrough(self, left_ibis_table):
        """Test that existing Ibis table passes through unchanged."""
        # Use class methods directly

        # Get the backend
        backend = IbisJoinStrategy._get_ibis_backend(left_ibis_table)

        # Resolve with same backend should return same table
        result = IbisJoinStrategy._resolve_ibis_table(left_ibis_table, target_ibis_backend=backend)

        assert isinstance(result, ibis.expr.types.Table)
        # Should be the same table or equivalent
        assert result is not None

    def test_resolve_with_tablename_prefix(self, left_pandas_df):
        """Test resolving with tablename prefix."""
        # Use class methods directly
        ibis_table = IbisJoinStrategy._resolve_ibis_table(
            left_pandas_df,
            tablename_prefix="test_prefix"
        )

        assert isinstance(ibis_table, ibis.expr.types.Table)

    def test_resolve_with_temp_flag(self, left_pandas_df):
        """Test resolving with temp table flag."""
        # Use class methods directly

        # Initialize a backend
        backend = IbisJoinStrategy._init_ibis_connection("duckdb")

        ibis_table = IbisJoinStrategy._resolve_ibis_table(
            left_pandas_df,
            target_ibis_backend=backend,
            temp=True
        )

        assert isinstance(ibis_table, ibis.expr.types.Table)


@pytest.mark.unit
class TestIbisExecuteOnParameter:
    """Test execute_on parameter for controlling join execution location."""

    def test_resolve_join_backend_left(self, left_ibis_table, right_ibis_table):
        """Test resolving join backend with execute_on='left'."""
        # Use class methods directly

        backend = IbisJoinStrategy._resolve_join_backend(
            left_ibis_table,
            right_ibis_table,
            execute_on="left"
        )

        # Should return left backend
        left_backend = IbisJoinStrategy._get_ibis_backend(left_ibis_table)
        assert backend == left_backend

    def test_resolve_join_backend_right(self, left_ibis_table, right_ibis_table):
        """Test resolving join backend with execute_on='right'."""
        # Use class methods directly

        backend = IbisJoinStrategy._resolve_join_backend(
            left_ibis_table,
            right_ibis_table,
            execute_on="right"
        )

        # Should return right backend
        right_backend = IbisJoinStrategy._get_ibis_backend(right_ibis_table)
        assert backend == right_backend

    def test_resolve_join_backend_none(self, left_ibis_table, right_ibis_table):
        """Test resolving join backend with execute_on=None."""
        # Use class methods directly

        backend = IbisJoinStrategy._resolve_join_backend(
            left_ibis_table,
            right_ibis_table,
            execute_on=None
        )

        # Should return None (local memory execution)
        assert backend is None

    def test_join_with_execute_on_left(self, left_ibis_table, right_ibis_table):
        """Test join execution on left backend."""
        # Use class methods directly

        result = IbisJoinStrategy.inner_join(
            left_ibis_table,
            right_ibis_table,
            predicates="id",
            execute_on="left"
        )

        assert isinstance(result, ibis.expr.types.Table)

    def test_join_with_execute_on_right(self, left_ibis_table, right_ibis_table):
        """Test join execution on right backend."""
        # Use class methods directly

        result = IbisJoinStrategy.inner_join(
            left_ibis_table,
            right_ibis_table,
            predicates="id",
            execute_on="right"
        )

        assert isinstance(result, ibis.expr.types.Table)


@pytest.mark.unit
class TestIbisCrossBackendJoins:
    """Test joining DataFrames from different backends via Ibis."""

    def test_join_pandas_with_polars_via_ibis(self, left_pandas_df, right_polars_df):
        """Test joining pandas and Polars DataFrames via Ibis."""
        # Use class methods directly

        result = IbisJoinStrategy.inner_join(
            left_pandas_df,
            right_polars_df,
            predicates="id"
        )

        assert isinstance(result, ibis.expr.types.Table)

        # Execute and verify
        result_df = result.execute()
        assert len(result_df) == 3

    def test_join_ibis_with_pandas(self, left_ibis_table, right_pandas_df):
        """Test joining Ibis table with pandas DataFrame."""
        # Use class methods directly

        result = IbisJoinStrategy.inner_join(
            left_ibis_table,
            right_pandas_df,
            predicates="id"
        )

        assert isinstance(result, ibis.expr.types.Table)

        result_df = result.execute()
        assert len(result_df) == 3

    def test_join_ibis_with_polars(self, left_ibis_table, right_polars_df):
        """Test joining Ibis table with Polars DataFrame."""
        # Use class methods directly

        result = IbisJoinStrategy.inner_join(
            left_ibis_table,
            right_polars_df,
            predicates="id"
        )

        assert isinstance(result, ibis.expr.types.Table)

        result_df = result.execute()
        assert len(result_df) == 3


@pytest.mark.unit
class TestIbisJoinTableNaming:
    """Test table naming in Ibis joins."""

    def test_inner_join_table_prefix(self, left_ibis_table, right_ibis_table):
        """Test that inner join uses proper table name prefixes."""
        # Use class methods directly

        # Join should generate unique table names with prefixes
        result = IbisJoinStrategy._inner_join(
            left_ibis_table,
            right_ibis_table,
            predicates="id"
        )

        # Result should be a valid Ibis table
        assert isinstance(result, ibis.expr.types.Table)

    def test_left_join_table_prefix(self, left_ibis_table, right_ibis_table):
        """Test that left join uses proper table name prefixes."""
        # Use class methods directly

        result = IbisJoinStrategy._left_join(
            left_ibis_table,
            right_ibis_table,
            predicates="id"
        )

        assert isinstance(result, ibis.expr.types.Table)

    def test_outer_join_table_prefix(self, left_ibis_table, right_ibis_table):
        """Test that outer join uses proper table name prefixes."""
        # Use class methods directly

        result = IbisJoinStrategy._outer_join(
            left_ibis_table,
            right_ibis_table,
            predicates="id"
        )

        assert isinstance(result, ibis.expr.types.Table)


@pytest.mark.unit
class TestIbisJoinBothTableResolution:
    """Test resolving both tables to Ibis for joins."""

    def test_resolve_both_ibis_tables_default(self, left_ibis_table, right_ibis_table):
        """Test resolving both tables with default settings."""
        # Use class methods directly

        left_result, right_result = IbisJoinStrategy._resolve_both_ibis_tables(
            left_ibis_table,
            right_ibis_table
        )

        assert isinstance(left_result, ibis.expr.types.Table)
        assert isinstance(right_result, ibis.expr.types.Table)

    def test_resolve_both_tables_execute_on_left(self, left_ibis_table, right_ibis_table):
        """Test resolving both tables with execute_on='left'."""
        # Use class methods directly

        left_result, right_result = IbisJoinStrategy._resolve_both_ibis_tables(
            left_ibis_table,
            right_ibis_table,
            execute_on="left"
        )

        assert isinstance(left_result, ibis.expr.types.Table)
        assert isinstance(right_result, ibis.expr.types.Table)

    def test_resolve_both_tables_execute_on_right(self, left_ibis_table, right_ibis_table):
        """Test resolving both tables with execute_on='right'."""
        # Use class methods directly

        left_result, right_result = IbisJoinStrategy._resolve_both_ibis_tables(
            left_ibis_table,
            right_ibis_table,
            execute_on="right"
        )

        assert isinstance(left_result, ibis.expr.types.Table)
        assert isinstance(right_result, ibis.expr.types.Table)

    def test_resolve_mixed_backends_to_ibis(self, left_pandas_df, right_polars_df):
        """Test resolving mixed backend DataFrames to Ibis."""
        # Use class methods directly

        left_result, right_result = IbisJoinStrategy._resolve_both_ibis_tables(
            left_pandas_df,
            right_polars_df
        )

        assert isinstance(left_result, ibis.expr.types.Table)
        assert isinstance(right_result, ibis.expr.types.Table)


@pytest.mark.unit
class TestIbisJoinKwargs:
    """Test Ibis join with additional kwargs."""

    def test_inner_join_with_suffixes(self, left_ibis_table, right_ibis_table):
        """Test inner join with suffixes for overlapping columns."""
        # Use class methods directly

        result = IbisJoinStrategy.inner_join(
            left_ibis_table,
            right_ibis_table,
            predicates="id",
            lname="left_{name}",
            rname="right_{name}",
            # suffixes=("_left", "_right")
        )

        assert isinstance(result, ibis.expr.types.Table)




@pytest.mark.unit
class TestIbisJoinDataPreservation:
    """Test that Ibis joins preserve data correctly."""

    def test_inner_join_data_preservation(self, left_ibis_table, right_ibis_table):
        """Test that inner join preserves correct data."""
        # Use class methods directly

        result = IbisJoinStrategy.inner_join(left_ibis_table, right_ibis_table, predicates="id")

        # Execute and verify
        result_df = result.execute()

        # Check specific data
        row_2 = result_df[result_df['id'] == 2].iloc[0]
        assert row_2['name'] == "Bob"
        assert row_2['salary'] == 75000.0

    def test_left_join_preserves_all_left(self, left_ibis_table, right_ibis_table):
        """Test that left join preserves all left table data."""
        # Use class methods directly

        result = IbisJoinStrategy.left_join(left_ibis_table, right_ibis_table, predicates="id")

        # Execute and verify
        result_df = result.execute()

        # Get left table data
        left_df = left_ibis_table.execute()

        # All left IDs should be in result
        left_ids = set(left_df['id'])
        result_ids = set(result_df['id'])

        assert left_ids.issubset(result_ids)

    def test_outer_join_includes_all_data(self, left_ibis_table, right_ibis_table):
        """Test that outer join includes all data from both tables.

        Note: Ibis outer joins may create duplicate column names for join keys.
        We check for IDs in both 'id' column and potential 'id_right' column.
        """
        # Use class methods directly

        result = IbisJoinStrategy.outer_join(left_ibis_table, right_ibis_table, predicates="id")

        # Execute and verify
        result_df = result.execute()

        left_df = left_ibis_table.execute()
        right_df = right_ibis_table.execute()

        # All IDs from both tables should be in result
        left_ids = set(left_df['id'])
        right_ids = set(right_df['id'])

        # Get IDs from result, checking both 'id' and potentially 'id_right' columns
        import pandas as pd
        result_ids = set(result_df['id'].dropna()) if 'id' in result_df.columns else set()
        if 'id_right' in result_df.columns:
            result_ids = result_ids.union(set(result_df['id_right'].dropna()))

        all_ids = left_ids.union(right_ids)
        assert all_ids == result_ids
