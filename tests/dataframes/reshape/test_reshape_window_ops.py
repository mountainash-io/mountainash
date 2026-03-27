"""Tests for reshape module operations on windowed dataframes.

This module tests whether reshape operations work correctly on DataFrames
that have window operations applied. It tests across all supported backends
(pandas, polars, ibis, narwhals) in a parameterized fashion.

Key architectural differences:
1. **Pandas**: Creates intermediate window objects (Rolling, Expanding, EWM)
   that must be aggregated before becoming DataFrames
2. **Polars/Ibis/Narwhals**: Window operations return regular DataFrames/Tables
   directly, no intermediate objects

Expected behaviors:
1. Pandas window objects should NOT be supported by factory (require aggregation)
2. Windowed DataFrames (after window operations applied) should work normally
3. Results should be consistent across backends
"""

import pytest
from pytest_check import check
import pandas as pd
import polars as pl

from mountainash.dataframes.select import DataFrameSelectFactory
from mountainash.dataframes.introspect import DataFrameIntrospectFactory


# Pandas window object fixtures (intermediate objects)
PANDAS_WINDOW_FIXTURES = [
    "windowed_pandas_rolling",
    "windowed_pandas_expanding",
    "windowed_pandas_ewm",
    "windowed_pandas_groupby_rolling"
]

# Windowed result DataFrame fixtures (after window ops applied)
WINDOWED_RESULT_FIXTURES = [
    "windowed_polars_with_over",
    "windowed_polars_lazyframe_with_over",
    "windowed_ibis_with_over",
    "windowed_narwhals_with_over"
]


@pytest.mark.unit
class TestPandasWindowObjectDetection:
    """Test that the factory correctly handles (or rejects) pandas window objects."""

    @pytest.mark.parametrize("window_fixture", PANDAS_WINDOW_FIXTURES)
    def test_factory_detects_pandas_window_objects(self, window_fixture, request):
        """Test that factory rejects pandas window intermediate objects.

        Pandas window objects (Rolling, Expanding, EWM) are intermediate objects
        that must be aggregated (e.g., .sum(), .mean()) before becoming DataFrames.
        The factory should raise a clear ValueError for these types.
        """
        window_obj = request.getfixturevalue(window_fixture)

        # Try to get strategy - should fail for window objects
        with pytest.raises(ValueError, match="No strategy key found"):
            DataFrameSelectFactory.get_strategy(window_obj)

        print(f"✓ Factory correctly rejects pandas window object: {window_fixture}")

    def test_pandas_rolling_type_detection(self, windowed_pandas_rolling):
        """Test pandas Rolling object type detection."""
        check.is_instance(windowed_pandas_rolling, pd.core.window.rolling.Rolling)
        print(f"Pandas Rolling type: {type(windowed_pandas_rolling)}")

    def test_pandas_expanding_type_detection(self, windowed_pandas_expanding):
        """Test pandas Expanding object type detection."""
        check.is_instance(windowed_pandas_expanding, pd.core.window.expanding.Expanding)
        print(f"Pandas Expanding type: {type(windowed_pandas_expanding)}")

    def test_pandas_ewm_type_detection(self, windowed_pandas_ewm):
        """Test pandas EWM object type detection."""
        check.is_instance(windowed_pandas_ewm, pd.core.window.ewm.ExponentialMovingWindow)
        print(f"Pandas EWM type: {type(windowed_pandas_ewm)}")

    def test_pandas_groupby_rolling_type_detection(self, windowed_pandas_groupby_rolling):
        """Test pandas GroupBy Rolling object type detection."""
        check.is_instance(windowed_pandas_groupby_rolling, pd.core.window.rolling.RollingGroupby)
        print(f"Pandas GroupBy Rolling type: {type(windowed_pandas_groupby_rolling)}")


@pytest.mark.unit
class TestPandasWindowAggregation:
    """Test that pandas window aggregation produces regular DataFrames."""

    def test_pandas_rolling_aggregation(self, windowed_pandas_rolling):
        """Test that pandas rolling window can be aggregated to DataFrame."""
        # Aggregate the window object
        result = windowed_pandas_rolling.sum()

        check.is_instance(result, pd.DataFrame, "Aggregation should return DataFrame")
        check.greater(len(result), 0, "Result should have rows")

        # Now the result should work with factory
        strategy = DataFrameSelectFactory.get_strategy(result)
        check.is_not_none(strategy)
        print(f"✓ Pandas rolling aggregation produces DataFrame that works with factory")

    def test_pandas_expanding_aggregation(self, windowed_pandas_expanding):
        """Test that pandas expanding window can be aggregated to DataFrame."""
        result = windowed_pandas_expanding.sum()

        check.is_instance(result, pd.DataFrame)
        strategy = DataFrameSelectFactory.get_strategy(result)
        check.is_not_none(strategy)
        print(f"✓ Pandas expanding aggregation produces DataFrame that works with factory")

    def test_pandas_ewm_aggregation(self, windowed_pandas_ewm):
        """Test that pandas EWM window can be aggregated to DataFrame."""
        result = windowed_pandas_ewm.mean()

        check.is_instance(result, pd.DataFrame)
        strategy = DataFrameSelectFactory.get_strategy(result)
        check.is_not_none(strategy)
        print(f"✓ Pandas EWM aggregation produces DataFrame that works with factory")


@pytest.mark.unit
class TestWindowedDataFrameSupport:
    """Test that windowed DataFrames (after window ops applied) work with reshape."""

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_factory_supports_windowed_dataframes(self, windowed_fixture, request):
        """Test that factory supports DataFrames with window operations applied.

        Unlike pandas window intermediate objects, windowed DataFrames from
        polars/ibis/narwhals should work normally with the factory.
        """
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(windowed_df)
            check.is_not_none(strategy, f"Strategy should be returned for {windowed_fixture}")
            print(f"✓ Factory supports windowed DataFrame: {windowed_fixture} -> {strategy}")
        except ValueError as e:
            pytest.fail(f"Factory should support windowed DataFrame {windowed_fixture}: {e}")

    def test_polars_windowed_dataframe_type(self, windowed_polars_with_over):
        """Test that polars window operation returns regular DataFrame."""
        check.is_instance(windowed_polars_with_over, pl.DataFrame)
        print(f"✓ Polars window operation returns DataFrame: {type(windowed_polars_with_over)}")

    def test_polars_lazy_windowed_type(self, windowed_polars_lazyframe_with_over):
        """Test that polars lazy window operation returns LazyFrame."""
        check.is_instance(windowed_polars_lazyframe_with_over, pl.LazyFrame)
        print(f"✓ Polars lazy window operation returns LazyFrame: {type(windowed_polars_lazyframe_with_over)}")


@pytest.mark.unit
class TestWindowedDataFrameColumnOperations:
    """Test column operations on windowed DataFrames."""

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_select_on_windowed_dataframe(self, windowed_fixture, request):
        """Test select operation on windowed DataFrame."""
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(windowed_df)
            columns = strategy.column_names(windowed_df)

            # Select first available column
            if len(columns) > 0:
                result = strategy.select(windowed_df, columns[0])
                check.is_not_none(result)
                print(f"✓ Select works on windowed {windowed_fixture}")
        except Exception as e:
            pytest.fail(f"Select should work on windowed DataFrame {windowed_fixture}: {e}")

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_drop_on_windowed_dataframe(self, windowed_fixture, request):
        """Test drop operation on windowed DataFrame."""
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(windowed_df)
            columns = strategy.column_names(windowed_df)

            # Drop last column if multiple columns exist
            if len(columns) > 1:
                result = strategy.drop(windowed_df, columns[-1])
                check.is_not_none(result)
                print(f"✓ Drop works on windowed {windowed_fixture}")
        except Exception as e:
            pytest.fail(f"Drop should work on windowed DataFrame {windowed_fixture}: {e}")

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_rename_on_windowed_dataframe(self, windowed_fixture, request):
        """Test rename operation on windowed DataFrame."""
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(windowed_df)
            columns = strategy.column_names(windowed_df)

            # Rename first column if it exists
            if len(columns) > 0:
                mapping = {columns[0]: f"{columns[0]}_renamed"}
                result = strategy.rename(windowed_df, mapping)
                check.is_not_none(result)
                print(f"✓ Rename works on windowed {windowed_fixture}")
        except Exception as e:
            pytest.fail(f"Rename should work on windowed DataFrame {windowed_fixture}: {e}")


@pytest.mark.unit
class TestWindowedDataFrameRowOperations:
    """Test row operations on windowed DataFrames."""

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_head_on_windowed_dataframe(self, windowed_fixture, request):
        """Test head operation on windowed DataFrame."""
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(windowed_df)
            result = strategy.head(windowed_df, 3)
            check.is_not_none(result)

            # Verify row count
            count = strategy.count(result)
            check.less_equal(count, 3)
            print(f"✓ Head works on windowed {windowed_fixture}")
        except Exception as e:
            pytest.fail(f"Head should work on windowed DataFrame {windowed_fixture}: {e}")

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_count_on_windowed_dataframe(self, windowed_fixture, request):
        """Test count operation on windowed DataFrame."""
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(windowed_df)
            count = strategy.count(windowed_df)
            check.is_instance(count, int)
            check.greater_equal(count, 0)
            print(f"✓ Count works on windowed {windowed_fixture}: {count}")
        except Exception as e:
            pytest.fail(f"Count should work on windowed DataFrame {windowed_fixture}: {e}")

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_split_in_batches_on_windowed_dataframe(self, windowed_fixture, request):
        """Test split_in_batches operation on windowed DataFrame."""
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(windowed_df)
            batches, total = strategy.split_in_batches(windowed_df, batch_size=2)
            check.is_instance(batches, list)
            check.greater(len(batches), 0)
            check.greater(total, 0)
            print(f"✓ Split_in_batches works on windowed {windowed_fixture}")
        except Exception as e:
            pytest.fail(f"Split_in_batches should work on windowed DataFrame {windowed_fixture}: {e}")


@pytest.mark.unit
class TestWindowedDataFrameIntrospection:
    """Test introspection methods on windowed DataFrames."""

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_column_names_on_windowed_dataframe(self, windowed_fixture, request):
        """Test column_names introspection on windowed DataFrame."""
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameSelectFactory.get_strategy(windowed_df)
            columns = strategy.column_names(windowed_df)
            check.is_instance(columns, list)
            check.greater(len(columns), 0)
            print(f"✓ Column_names works on windowed {windowed_fixture}: {columns}")
        except Exception as e:
            pytest.fail(f"Column_names should work on windowed DataFrame {windowed_fixture}: {e}")

    @pytest.mark.parametrize("windowed_fixture", WINDOWED_RESULT_FIXTURES)
    def test_shape_on_windowed_dataframe(self, windowed_fixture, request):
        """Test shape introspection on windowed DataFrame."""
        windowed_df = request.getfixturevalue(windowed_fixture)

        try:
            strategy = DataFrameIntrospectFactory.get_strategy(windowed_df)
            shape = strategy.shape(windowed_df)
            check.is_not_none(shape)
            print(f"✓ Shape works on windowed {windowed_fixture}: {shape}")
        except Exception as e:
            pytest.fail(f"Shape should work on windowed DataFrame {windowed_fixture}: {e}")


@pytest.mark.unit
class TestWindowWorkflow:
    """Test realistic workflows with window operations.

    Documents the expected patterns for working with window operations,
    showing differences between pandas and other backends.
    """

    def test_pandas_window_then_aggregate_then_reshape(self, windowed_pandas_rolling):
        """Test pandas workflow: window -> aggregate -> reshape.

        This is the expected pattern for pandas - create window object,
        aggregate it to get a DataFrame, then perform reshape operations.
        """
        # Aggregate window object first (this is the key step)
        aggregated = windowed_pandas_rolling.sum()

        # Now reshape operations should work on the aggregated dataframe
        strategy = DataFrameSelectFactory.get_strategy(aggregated)

        # Test select
        selected = strategy.select(aggregated, ["id", "value"])
        check.is_not_none(selected)

        # Test head
        subset = strategy.head(selected, 3)
        check.is_not_none(subset)

        print(f"✓ Pandas workflow: window -> aggregate -> reshape works")

    def test_polars_window_returns_dataframe_directly(self, windowed_polars_with_over):
        """Test that polars window operations return DataFrames directly.

        Unlike pandas, polars window operations return regular DataFrames
        that can be used immediately with reshape operations.
        """
        # Polars window operations return DataFrames directly
        check.is_instance(windowed_polars_with_over, pl.DataFrame)

        # Reshape operations work immediately, no aggregation needed
        strategy = DataFrameSelectFactory.get_strategy(windowed_polars_with_over)

        # Test operations
        columns = strategy.column_names(windowed_polars_with_over)
        check.greater(len(columns), 0)

        subset = strategy.head(windowed_polars_with_over, 3)
        check.is_not_none(subset)


    def test_polars_lazy_window_preserves_laziness(self, windowed_polars_lazyframe_with_over):
        """Test that polars lazy window operations maintain laziness."""
        # Window operations on LazyFrame return LazyFrame
        check.is_instance(windowed_polars_lazyframe_with_over, pl.LazyFrame)

        # Get strategy for LazyFrame
        strategy = DataFrameSelectFactory.get_strategy(windowed_polars_lazyframe_with_over)

        # Operations should preserve laziness
        selected = strategy.select(windowed_polars_lazyframe_with_over, ["id", "category"])
        check.is_instance(selected, pl.LazyFrame)

        # Only collect at the end
        result = selected.collect()
        check.is_instance(result, pl.DataFrame)



@pytest.mark.unit
class TestWindowDocumentation:
    """Document current window operation support status for each backend."""

    def test_document_pandas_window_support(self, all_pandas_window_objects):
        """Document pandas window object support status."""
        print("\n" + "="*60)
        print("PANDAS WINDOW OPERATIONS SUPPORT STATUS")
        print("="*60)

        for window_type, window_obj in all_pandas_window_objects.items():
            print(f"\n{window_type.upper()}:")
            print(f"  Type: {type(window_obj).__name__}")
            print(f"  Module: {type(window_obj).__module__}")

            try:
                strategy = DataFrameSelectFactory.get_strategy(window_obj)
                print(f"  ✓ Supported by factory: {strategy.__name__}")
            except ValueError:
                print(f"  ✗ Not supported by factory (requires aggregation first)")
            except Exception as e:
                print(f"  ? Unexpected error: {e}")

        print("\n" + "="*60)
        print("PANDAS RECOMMENDATION:")
        print("Window objects must be aggregated before using reshape operations:")
        print("  1. df.rolling(window=3) or df.expanding() or df.ewm(span=3)")
        print("  2. .sum() or .mean() or other aggregation")
        print("  3. Then use reshape operations (select, drop, rename, etc.)")
        print("="*60)

    def test_document_all_backends_window_support(self):
        """Document window operation support across all backends."""
        print("\n" + "="*60)
        print("WINDOW OPERATIONS SUPPORT - ALL BACKENDS")
        print("="*60)

        print("\nPANDAS:")
        print("  Window Type: Intermediate objects (Rolling, Expanding, EWM)")
        print("  Factory Support: ✗ (intermediate objects not supported)")
        print("  Workflow: window() -> aggregate() -> DataFrame -> reshape ops")

        print("\nPOLARS:")
        print("  Window Type: Expressions with .over() return DataFrame directly")
        print("  Factory Support: ✓ (returns regular DataFrame)")
        print("  Workflow: with_columns([...over()]) -> DataFrame -> reshape ops")

        print("\nPOLARS LAZYFRAME:")
        print("  Window Type: Expressions with .over() return LazyFrame directly")
        print("  Factory Support: ✓ (returns regular LazyFrame)")
        print("  Workflow: with_columns([...over()]) -> LazyFrame -> reshape ops")

        print("\nIBIS:")
        print("  Window Type: Expressions with .over() return Table directly")
        print("  Factory Support: ✓ (returns regular Table)")
        print("  Workflow: mutate(...over(window)) -> Table -> reshape ops")

        print("\nNARWHALS:")
        print("  Window Type: Depends on underlying backend")
        print("  Factory Support: ✓ (returns regular DataFrame)")
        print("  Workflow: Backend-specific, typically returns DataFrame")

        print("\n" + "="*60)
        print("KEY INSIGHT:")
        print("Only pandas creates intermediate window objects that require")
        print("aggregation. All other backends return regular DataFrames/Tables")
        print("directly from window operations, which work immediately with")
        print("reshape operations.")
        print("="*60)
