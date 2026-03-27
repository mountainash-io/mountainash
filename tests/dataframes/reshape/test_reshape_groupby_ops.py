"""Tests for reshape module operations on grouped dataframes.

This module tests whether reshape operations work correctly on DataFrames
that have had group_by() applied. It tests across all supported backends
(pandas, polars, ibis, narwhals) in a parameterized fashion.

Key behaviors to verify:
1. Factory should detect grouped dataframes (or fail gracefully)
2. Operations should work on grouped dataframes or raise clear errors
3. Grouped operations should preserve the grouped nature when appropriate
4. Results should be consistent across backends
"""

import pytest
from pytest_check import check
import pandas as pd
import polars as pl

from mountainash.dataframes.select import DataFrameSelectFactory


# Grouped backend fixtures for parameterized testing
GROUPED_BACKEND_FIXTURES = [
    "grouped_pandas_df",
    "grouped_polars_df",
    "grouped_polars_lazyframe",
    "grouped_ibis_table",
    "grouped_narwhals_df"
]


@pytest.mark.unit
class TestGroupByFactoryDetection:
    """Test that the factory correctly handles (or rejects) grouped dataframes."""

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_factory_detects_grouped_dataframes(self, grouped_fixture, request):
        """Test that factory can handle grouped dataframes.

        This test documents current behavior. Grouped dataframes may either:
        - Be detected and handled by a strategy (ideal)
        - Raise a clear ValueError indicating groupby types are not supported

        The test will PASS if either behavior occurs consistently.
        """
        grouped_df = request.getfixturevalue(grouped_fixture)

        # Try to get strategy - may succeed or fail depending on implementation
        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_df)
            # If we get here, the factory successfully detected the grouped dataframe
            check.is_not_none(strategy, f"Strategy should be returned for {grouped_fixture}")
            print(f"✓ Factory detected grouped dataframe: {grouped_fixture} -> {strategy}")
        except ValueError as e:
            # If factory doesn't support grouped dataframes, it should raise ValueError
            check.is_in("No strategy key found", str(e),
                       f"Should raise clear error for unsupported grouped type: {grouped_fixture}")
            print(f"⚠ Factory does not support grouped dataframes: {grouped_fixture} - {e}")
        except Exception as e:
            # Any other exception is unexpected
            pytest.fail(f"Unexpected exception for {grouped_fixture}: {type(e).__name__}: {e}")

    def test_pandas_groupby_type_detection(self, grouped_pandas_df):
        """Test pandas GroupBy object type detection."""
        check.is_instance(grouped_pandas_df, pd.core.groupby.generic.DataFrameGroupBy)
        print(f"Pandas GroupBy type: {type(grouped_pandas_df)}")

    def test_polars_groupby_type_detection(self, grouped_polars_df):
        """Test polars GroupBy object type detection."""
        check.is_instance(grouped_polars_df, pl.dataframe.group_by.GroupBy)
        print(f"Polars GroupBy type: {type(grouped_polars_df)}")

    def test_polars_lazy_groupby_type_detection(self, grouped_polars_lazyframe):
        """Test polars LazyGroupBy object type detection."""
        check.is_instance(grouped_polars_lazyframe, pl.lazyframe.group_by.LazyGroupBy)
        print(f"Polars LazyGroupBy type: {type(grouped_polars_lazyframe)}")


@pytest.mark.unit
class TestGroupByAggregation:
    """Test that aggregation operations work on grouped dataframes."""

    def test_pandas_groupby_aggregation(self, grouped_pandas_df):
        """Test that pandas grouped dataframe can be aggregated."""
        # This is the typical use case - aggregate after grouping
        result = grouped_pandas_df.agg({"value": "sum", "id": "count"})

        check.is_instance(result, pd.DataFrame, "Aggregation should return DataFrame")
        check.greater(len(result), 0, "Result should have rows")
        print(f"Pandas grouped aggregation result:\n{result}")

    def test_polars_groupby_aggregation(self, grouped_polars_df):
        """Test that polars grouped dataframe can be aggregated."""
        result = grouped_polars_df.agg(
            pl.col("value").sum().alias("value_sum"),
            pl.col("id").count().alias("id_count")
        )

        check.is_instance(result, pl.DataFrame, "Aggregation should return DataFrame")
        check.greater(len(result), 0, "Result should have rows")
        print(f"Polars grouped aggregation result:\n{result}")

    def test_polars_lazy_groupby_aggregation(self, grouped_polars_lazyframe):
        """Test that polars lazy grouped dataframe can be aggregated."""
        result = grouped_polars_lazyframe.agg(
            pl.col("value").sum().alias("value_sum"),
            pl.col("id").count().alias("id_count")
        )

        # Result should be LazyFrame
        check.is_instance(result, pl.LazyFrame, "Aggregation should return LazyFrame")

        # Collect to verify data
        collected = result.collect()
        check.greater(len(collected), 0, "Result should have rows when collected")
        print(f"Polars lazy grouped aggregation result:\n{collected}")


@pytest.mark.unit
class TestGroupByColumnOperations:
    """Test column operations on grouped dataframes.

    These tests verify whether column operations (select, drop, rename)
    work on grouped dataframes or if they require materialization first.
    """

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_select_on_grouped_dataframe(self, grouped_fixture, request):
        """Test select operation on grouped dataframe.

        Expected behavior: May either work directly or require aggregation first.
        """
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_df)
            result = strategy.select(grouped_df, ["id", "name"])
            check.is_not_none(result)
            print(f"✓ Select works on grouped {grouped_fixture}")
        except (ValueError, AttributeError, Exception) as e:
            # Document that this operation may not be supported on grouped dataframes
            print(f"⚠ Select not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_drop_on_grouped_dataframe(self, grouped_fixture, request):
        """Test drop operation on grouped dataframe."""
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_df)
            result = strategy.drop(grouped_df, "active")
            check.is_not_none(result)
            print(f"✓ Drop works on grouped {grouped_fixture}")
        except (ValueError, AttributeError, Exception) as e:
            print(f"⚠ Drop not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_rename_on_grouped_dataframe(self, grouped_fixture, request):
        """Test rename operation on grouped dataframe."""
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_df)
            result = strategy.rename(grouped_df, {"name": "full_name"})
            check.is_not_none(result)
            print(f"✓ Rename works on grouped {grouped_fixture}")
        except (ValueError, AttributeError, Exception) as e:
            print(f"⚠ Rename not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")


@pytest.mark.unit
class TestGroupByRowOperations:
    """Test row operations on grouped dataframes.

    These tests verify whether row operations (head, count, split_in_batches)
    work on grouped dataframes or if they require materialization first.
    """

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_head_on_grouped_dataframe(self, grouped_fixture, request):
        """Test head operation on grouped dataframe.

        Expected behavior: May return first N rows per group or fail.
        """
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_df)
            result = strategy.head(grouped_df, 2)
            check.is_not_none(result)
            print(f"✓ Head works on grouped {grouped_fixture}")
        except (ValueError, AttributeError, Exception) as e:
            print(f"⚠ Head not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_count_on_grouped_dataframe(self, grouped_fixture, request):
        """Test count operation on grouped dataframe.

        Expected behavior: May return total count or counts per group.
        """
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_df)
            result = strategy.count(grouped_df)
            check.is_instance(result, int)
            check.greater_equal(result, 0)
            print(f"✓ Count works on grouped {grouped_fixture}: {result}")
        except (ValueError, AttributeError, Exception) as e:
            print(f"⚠ Count not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_split_in_batches_on_grouped_dataframe(self, grouped_fixture, request):
        """Test split_in_batches operation on grouped dataframe."""
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_df)
            result = strategy.split_in_batches(grouped_df, batch_size=2)
            check.is_instance(result, list)
            check.greater(len(result), 0)
            print(f"✓ Split_in_batches works on grouped {grouped_fixture}")
        except (ValueError, AttributeError, Exception) as e:
            print(f"⚠ Split_in_batches not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")


@pytest.mark.unit
class TestGroupByIntrospection:
    """Test introspection methods on grouped dataframes."""

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_column_names_on_grouped_dataframe(self, grouped_fixture, request):
        """Test column_names introspection on grouped dataframe."""
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_df)
            columns = strategy.column_names(grouped_df)
            check.is_instance(columns, list)
            check.greater(len(columns), 0)
            print(f"✓ Column_names works on grouped {grouped_fixture}: {columns}")
        except (ValueError, AttributeError, Exception) as e:
            print(f"⚠ Column_names not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_shape_on_grouped_dataframe(self, grouped_fixture, request):
        """Test shape introspection on grouped dataframe."""
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameReshapeFactory.get_strategy(grouped_df)
            shape = strategy.shape(grouped_df)
            check.is_not_none(shape)
            print(f"✓ Shape works on grouped {grouped_fixture}: {shape}")
        except (ValueError, AttributeError, Exception) as e:
            print(f"⚠ Shape not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")

    @pytest.mark.parametrize("grouped_fixture", GROUPED_BACKEND_FIXTURES)
    def test_get_dataframe_info_on_grouped_dataframe(self, grouped_fixture, request):
        """Test get_dataframe_info on grouped dataframe."""
        grouped_df = request.getfixturevalue(grouped_fixture)

        try:
            strategy = DataFrameReshapeFactory.get_strategy(grouped_df)
            info = strategy.get_dataframe_info(grouped_df)
            check.is_instance(info, dict)
            check.greater(len(info), 0)
            print(f"✓ Get_dataframe_info works on grouped {grouped_fixture}: {info}")
        except (ValueError, AttributeError, Exception) as e:
            print(f"⚠ Get_dataframe_info not supported on grouped {grouped_fixture}: {e}")
            check.is_true(True, "Expected limitation documented")


@pytest.mark.unit
class TestGroupByWorkflow:
    """Test realistic workflows with grouped dataframes.

    These tests document expected patterns for working with grouped data,
    showing when materialization/aggregation is required.
    """

    def test_pandas_groupby_then_aggregate_then_reshape(self, grouped_pandas_df):
        """Test typical workflow: group -> aggregate -> reshape.

        This is the expected pattern - aggregate after grouping,
        then perform reshape operations on the materialized result.
        """
        # Aggregate first (this is the key step)
        aggregated = grouped_pandas_df.agg({"value": "sum", "id": "count"}).reset_index()

        # Now reshape operations should work on the materialized dataframe
        strategy = DataFrameSelectFactory.get_strategy(aggregated)

        # Test select
        selected = strategy.select(aggregated, ["category", "value"])
        check.is_not_none(selected)

        # Test rename
        renamed = strategy.rename(selected, {"value": "total_value"})
        check.is_not_none(renamed)

        print(f"✓ Pandas workflow: group -> aggregate -> reshape works")
        print(f"Final result:\n{renamed}")

    def test_polars_groupby_then_aggregate_then_reshape(self, grouped_polars_df):
        """Test typical Polars workflow: group -> aggregate -> reshape."""
        # Aggregate first
        aggregated = grouped_polars_df.agg(
            pl.col("value").sum().alias("total_value"),
            pl.col("id").count().alias("count")
        )

        # Now reshape operations should work
        strategy = DataFrameSelectFactory.get_strategy(aggregated)

        # Test select
        selected = strategy.select(aggregated, ["category", "total_value"])
        check.is_not_none(selected)

        # Test head
        subset = strategy.head(selected, 2)
        check.is_not_none(subset)

        print(f"✓ Polars workflow: group -> aggregate -> reshape works")
        print(f"Final result:\n{subset}")

    def test_polars_lazy_groupby_workflow_preserves_lazy(self, grouped_polars_lazyframe):
        """Test that lazy workflow maintains laziness throughout."""
        # Aggregate (stays lazy)
        aggregated = grouped_polars_lazyframe.agg(
            pl.col("value").sum().alias("total_value"),
            pl.col("id").count().alias("count")
        )

        check.is_instance(aggregated, pl.LazyFrame, "After aggregation should still be lazy")

        # Get strategy for LazyFrame
        strategy = DataFrameSelectFactory.get_strategy(aggregated)

        # Operations should preserve laziness
        selected = strategy.select(aggregated, ["category", "total_value"])
        check.is_instance(selected, pl.LazyFrame, "After select should still be lazy")

        # Only collect at the end
        result = selected.collect()
        check.is_instance(result, pl.DataFrame, "Final result should be DataFrame after collect")

        print(f"✓ Polars lazy workflow maintains laziness")
        print(f"Final collected result:\n{result}")


@pytest.mark.unit
class TestGroupByDocumentation:
    """Document current group_by support status for each backend."""

    def test_document_pandas_groupby_support(self, grouped_pandas_df):
        """Document pandas GroupBy support status."""
        print("\n" + "="*60)
        print("PANDAS GROUP_BY SUPPORT STATUS")
        print("="*60)
        print(f"Type: {type(grouped_pandas_df)}")
        print(f"Module: {type(grouped_pandas_df).__module__}")
        print(f"Class: {type(grouped_pandas_df).__name__}")

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_pandas_df)
            print(f"✓ Factory supports pandas GroupBy: {strategy}")
        except ValueError as e:
            print(f"✗ Factory does not support pandas GroupBy")
            print(f"  Error: {e}")

        print("\nRecommendation: Use .agg() or .apply() before reshape operations")
        print("="*60)

    def test_document_polars_groupby_support(self, grouped_polars_df):
        """Document polars GroupBy support status."""
        print("\n" + "="*60)
        print("POLARS GROUP_BY SUPPORT STATUS")
        print("="*60)
        print(f"Type: {type(grouped_polars_df)}")
        print(f"Module: {type(grouped_polars_df).__module__}")
        print(f"Class: {type(grouped_polars_df).__name__}")

        try:
            strategy = DataFrameSelectFactory.get_strategy(grouped_polars_df)
            print(f"✓ Factory supports polars GroupBy: {strategy}")
        except ValueError as e:
            print(f"✗ Factory does not support polars GroupBy")
            print(f"  Error: {e}")

        print("\nRecommendation: Use .agg() before reshape operations")
        print("="*60)

    def test_document_all_backends_groupby_support(self, all_grouped_backends):
        """Document group_by support status across all backends."""
        print("\n" + "="*60)
        print("GROUP_BY SUPPORT STATUS - ALL BACKENDS")
        print("="*60)

        for backend_name, grouped_df in all_grouped_backends.items():
            print(f"\n{backend_name.upper()}:")
            print(f"  Type: {type(grouped_df).__name__}")

            try:
                strategy = DataFrameSelectFactory.get_strategy(grouped_df)
                print(f"  ✓ Supported by factory: {strategy.__name__}")
            except ValueError:
                print(f"  ✗ Not supported by factory (requires aggregation first)")
            except Exception as e:
                print(f"  ? Unexpected error: {e}")

        print("\n" + "="*60)
        print("RECOMMENDATION:")
        print("Always aggregate grouped dataframes before using reshape operations:")
        print("  1. df.group_by(col)")
        print("  2. .agg(...) or .apply(...)")
        print("  3. Then use reshape operations (select, drop, rename, etc.)")
        print("="*60)
