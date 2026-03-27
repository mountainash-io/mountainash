"""Tests for reshape module row operations.

This module tests row manipulation methods (head, split_in_batches, get_first_row_as_dict)
across all backends.
"""

import pytest
from pytest_check import check

from mountainash.dataframes.select import DataFrameSelectFactory


# Backend fixtures for parameterized testing
BACKEND_FIXTURES = [
    "sample_pandas_df",
    "sample_polars_df",
    "sample_pyarrow_table",
    "real_ibis_table",
    "sample_narwhals_df"
]

# Backend fixtures for batching tests (includes lazy frames)
BATCHING_BACKEND_FIXTURES = [
    "large_dataframe_for_batching",         # pandas
    "large_polars_df_for_batching",         # polars eager
    "large_polars_lazyframe_for_batching",  # polars lazy
    "large_pyarrow_table_for_batching",     # pyarrow
    "large_ibis_table_for_batching",        # ibis
    "large_narwhals_df_for_batching",       # narwhals eager
    "large_narwhals_lazyframe_for_batching" # narwhals lazy
]


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestHeadOperation:
    """Test head() row operation across all backends."""

    def test_head_basic(self, backend_fixture, request):
        """Test head() returns correct number of rows."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        result = strategy.head(df, 3)

        # Verify result has at most 3 rows
        count = strategy.count(result)
        check.less_equal(count, 3)
        check.greater(count, 0)

    def test_head_n_zero(self, backend_fixture, request):
        """Test head(0) returns empty result."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        result = strategy.head(df, 0)

        count = strategy.count(result)
        check.equal(count, 0)

    def test_head_n_negative(self, backend_fixture, request):
        """Test head() with negative n raises ValueError."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        with pytest.raises(ValueError, match="greater than or equal to 0"):
            strategy.head(df, -1)

    def test_head_n_greater_than_rows(self, backend_fixture, request):
        """Test head() with n > row count returns all rows."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_count = strategy.count(df)
        result = strategy.head(df, 1000)

        result_count = strategy.count(result)
        check.equal(result_count, original_count)


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BATCHING_BACKEND_FIXTURES)
class TestSplitInBatches:
    """Test split_in_batches() operation across all backends including lazy frames."""

    def test_split_in_batches_basic(self, backend_fixture, request):
        """Test basic batch splitting."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches, total = strategy.split_in_batches(df, batch_size=25)

        # Should have 4 batches (100 rows / 25 per batch)
        check.is_instance(batches, list)
        check.equal(len(batches), 4)
        check.equal(total, 100, f"Total should be 100 rows for {backend_fixture}")

        # Verify each batch size
        for i, batch in enumerate(batches):
            # Get strategy for the batch (may be different from source df strategy)
            batch_strategy = DataFrameSelectFactory.get_strategy(batch)
            batch_count = batch_strategy.count(batch)
            check.equal(batch_count, 25, f"Batch {i} should have 25 rows for {backend_fixture}")

    def test_split_in_batches_exact_division(self, backend_fixture, request):
        """Test batching with exact division."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches, total = strategy.split_in_batches(df, batch_size=20)

        # Should have 5 batches (100 / 20)
        check.equal(len(batches), 5, f"Should have 5 batches for {backend_fixture}")
        check.equal(total, 100, f"Total should be 100 rows for {backend_fixture}")

    def test_split_in_batches_with_remainder(self, backend_fixture, request):
        """Test batching with remainder rows."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches, total = strategy.split_in_batches(df, batch_size=30)

        # Should have 4 batches (3 full + 1 partial)
        check.equal(len(batches), 4, f"Should have 4 batches for {backend_fixture}")
        check.equal(total, 100, f"Total should be 100 rows for {backend_fixture}")

        # Last batch should have 10 rows (100 - 90)
        last_batch_strategy = DataFrameSelectFactory.get_strategy(batches[-1])
        last_batch_count = last_batch_strategy.count(batches[-1])
        check.equal(last_batch_count, 10, f"Last batch should have 10 rows for {backend_fixture}")

    def test_split_in_batches_larger_than_df(self, backend_fixture, request):
        """Test batching when batch_size > DataFrame size."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches, total = strategy.split_in_batches(df, batch_size=200)

        # Should have 1 batch containing all rows
        check.equal(len(batches), 1, f"Should have 1 batch for {backend_fixture}")
        check.equal(total, 100, f"Total should be 100 rows for {backend_fixture}")
        batch_strategy = DataFrameSelectFactory.get_strategy(batches[0])
        check.equal(batch_strategy.count(batches[0]), 100, f"Batch should have 100 rows for {backend_fixture}")

    def test_split_in_batches_invalid_size(self, backend_fixture, request):
        """Test that batch_size <= 0 raises ValueError."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        with pytest.raises(ValueError, match="greater than 0"):
            strategy.split_in_batches(df, batch_size=0)

        with pytest.raises(ValueError, match="greater than 0"):
            strategy.split_in_batches(df, batch_size=-10)


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BACKEND_FIXTURES)
class TestRowOperationsPreserveStructure:
    """Test that row operations preserve DataFrame structure."""

    def test_head_preserves_columns(self, backend_fixture, request):
        """Test that head() preserves all columns."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_columns = strategy.column_names(df)
        result = strategy.head(df, 2)
        result_columns = strategy.column_names(result)

        # All columns should be preserved
        check.equal(sorted(result_columns), sorted(original_columns))


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BATCHING_BACKEND_FIXTURES)
class TestSplitPreservesStructure:
    """Test that split_in_batches() preserves DataFrame structure."""

    def test_split_preserves_columns(self, backend_fixture, request):
        """Test that split_in_batches() preserves all columns in each batch."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_columns = strategy.column_names(df)
        batches, total = strategy.split_in_batches(df, batch_size=25)

        # Each batch should have all columns
        for i, batch in enumerate(batches):
            batch_columns = strategy.column_names(batch)
            check.equal(
                sorted(batch_columns),
                sorted(original_columns),
                f"Batch {i} columns should match original for {backend_fixture}"
            )

    def test_split_preserves_data_integrity(self, backend_fixture, request):
        """Test that split_in_batches() preserves all data across batches."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_count = strategy.count(df)
        batches, total = strategy.split_in_batches(df, batch_size=25)

        # Total should match original count
        check.equal(total, original_count, f"Total should match original count for {backend_fixture}")

        # Sum of all batch counts should equal original count
        total_batch_count = sum(DataFrameSelectFactory.get_strategy(batch).count(batch) for batch in batches)
        check.equal(
            total_batch_count,
            original_count,
            f"Total batch count should equal original count for {backend_fixture}"
        )


@pytest.mark.unit
class TestSplitLazyFrameBehavior:
    """Test lazy frame specific behavior for split_in_batches().

    NOTE: split_in_batches() now materializes LazyFrames for efficiency
    (single execution instead of N+1). Use split_in_batches_generator()
    for truly lazy batching.
    """

    def test_polars_lazyframe_batches_are_eager(self, large_polars_lazyframe_for_batching):
        """Test that Polars LazyFrame batches are materialized (eager) after splitting."""
        import polars as pl

        df = large_polars_lazyframe_for_batching
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches, total = strategy.split_in_batches(df, batch_size=25)

        # Batches should be eager DataFrames (materialized for efficiency)
        for i, batch in enumerate(batches):
            check.is_instance(batch, pl.DataFrame, f"Batch {i} should be eager DataFrame")

        check.equal(total, 100, "Total should be 100 rows")

    def test_narwhals_lazyframe_batches_are_eager(self, large_narwhals_lazyframe_for_batching):
        """Test that Narwhals LazyFrame batches are materialized after splitting."""
        import narwhals as nw

        df = large_narwhals_lazyframe_for_batching
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches, total = strategy.split_in_batches(df, batch_size=25)

        # Batches should be eager (no collect method)
        for i, batch in enumerate(batches):
            native_batch = nw.to_native(batch)
            check.is_false(
                hasattr(native_batch, 'collect'),
                f"Batch {i} should be eager (no collect method)"
            )

        check.equal(total, 100, "Total should be 100 rows")

    def test_polars_lazyframe_batch_sizes(self, large_polars_lazyframe_for_batching):
        """Test that Polars LazyFrame batches have correct sizes."""
        df = large_polars_lazyframe_for_batching
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches, total = strategy.split_in_batches(df, batch_size=25)

        # Verify counts (no collection needed - already eager)
        for i, batch in enumerate(batches):
            batch_strategy = DataFrameSelectFactory.get_strategy(batch)
            batch_count = batch_strategy.count(batch)
            check.equal(batch_count, 25, f"Batch {i} should have 25 rows")

        check.equal(total, 100, "Total should be 100 rows")

    def test_narwhals_lazyframe_batch_sizes(self, large_narwhals_lazyframe_for_batching):
        """Test that Narwhals LazyFrame batches have correct sizes."""
        df = large_narwhals_lazyframe_for_batching
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches, total = strategy.split_in_batches(df, batch_size=25)

        # Verify counts (no collection needed - already eager)
        for i, batch in enumerate(batches):
            batch_strategy = DataFrameSelectFactory.get_strategy(batch)
            batch_count = batch_strategy.count(batch)
            check.equal(batch_count, 25, f"Batch {i} should have 25 rows")

        check.equal(total, 100, "Total should be 100 rows")


@pytest.mark.unit
class TestHeadLazyFrameBehavior:
    """Test lazy frame specific behavior for head() operation."""

    def test_head_polars_lazyframe_preserves_lazy(self, sample_polars_lazyframe):
        """Test that head() preserves Polars LazyFrame type."""
        import polars as pl

        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)
        result = strategy.head(sample_polars_lazyframe, 3)

        check.is_instance(result, pl.LazyFrame, "Result should remain Polars LazyFrame")

    def test_head_polars_lazyframe_various_n(self, sample_polars_lazyframe):
        """Test that head() with various n values preserves Polars LazyFrame type."""
        import polars as pl

        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        # Test n=0
        result_zero = strategy.head(sample_polars_lazyframe, 0)
        check.is_instance(result_zero, pl.LazyFrame, "head(0) should remain Polars LazyFrame")

        # Test n=1
        result_one = strategy.head(sample_polars_lazyframe, 1)
        check.is_instance(result_one, pl.LazyFrame, "head(1) should remain Polars LazyFrame")

        # Test n=10
        result_ten = strategy.head(sample_polars_lazyframe, 10)
        check.is_instance(result_ten, pl.LazyFrame, "head(10) should remain Polars LazyFrame")

    def test_head_polars_lazyframe_correctness(self, sample_polars_lazyframe):
        """Test that head() returns correct row count when collected."""
        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        result = strategy.head(sample_polars_lazyframe, 3)
        result_count = strategy.count(result)

        check.less_equal(result_count, 3, "head(3) should return at most 3 rows")
        check.greater(result_count, 0, "head(3) should return at least 1 row")

    def test_head_narwhals_lazyframe_preserves_lazy(self, sample_narwhals_lazyframe):
        """Test that head() preserves Narwhals LazyFrame type."""
        import narwhals as nw

        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_lazyframe)
        result = strategy.head(sample_narwhals_lazyframe, 3)

        # Convert to native to check underlying type
        native_result = nw.to_native(result)
        check.is_true(
            hasattr(native_result, 'collect'),
            "Result should have collect method (indicating it's lazy)"
        )

    def test_head_narwhals_lazyframe_correctness(self, sample_narwhals_lazyframe):
        """Test that head() returns correct row count when collected."""
        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_lazyframe)

        result = strategy.head(sample_narwhals_lazyframe, 3)
        result_count = strategy.count(result)

        check.less_equal(result_count, 3, "head(3) should return at most 3 rows")


@pytest.mark.unit
class TestLazyFrameRowColumnChaining:
    """Test that chaining row and column operations preserves laziness."""

    def test_select_head_chain_polars_lazy(self, sample_polars_lazyframe):
        """Test chaining select and head maintains Polars LazyFrame."""
        import polars as pl

        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        # Chain: select -> head
        selected = strategy.select(sample_polars_lazyframe, ["id", "name"])
        result = strategy.head(selected, 3)

        check.is_instance(selected, pl.LazyFrame, "After select should be LazyFrame")
        check.is_instance(result, pl.LazyFrame, "After head should be LazyFrame")

        # Verify correctness
        result_columns = strategy.column_names(result)
        check.equal(set(result_columns), {"id", "name"})
        check.less_equal(strategy.count(result), 3)

    def test_head_drop_chain_polars_lazy(self, sample_polars_lazyframe):
        """Test chaining head and drop maintains Polars LazyFrame."""
        import polars as pl

        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        # Chain: head -> drop
        subset = strategy.head(sample_polars_lazyframe, 3)
        result = strategy.drop(subset, "category")

        check.is_instance(subset, pl.LazyFrame, "After head should be LazyFrame")
        check.is_instance(result, pl.LazyFrame, "After drop should be LazyFrame")

    def test_rename_head_select_chain_polars_lazy(self, sample_polars_lazyframe):
        """Test complex row/column chaining maintains Polars LazyFrame."""
        import polars as pl

        strategy = DataFrameSelectFactory.get_strategy(sample_polars_lazyframe)

        # Chain: rename -> head -> select
        renamed = strategy.rename(sample_polars_lazyframe, {"name": "full_name"})
        subset = strategy.head(renamed, 3)
        result = strategy.select(subset, ["id", "full_name"])

        check.is_instance(renamed, pl.LazyFrame, "After rename should be LazyFrame")
        check.is_instance(subset, pl.LazyFrame, "After head should be LazyFrame")
        check.is_instance(result, pl.LazyFrame, "Final result should be LazyFrame")

        # Verify correctness
        result_columns = strategy.column_names(result)
        check.equal(set(result_columns), {"id", "full_name"})
        check.less_equal(strategy.count(result), 3)

    def test_select_head_chain_narwhals_lazy(self, sample_narwhals_lazyframe):
        """Test chaining select and head maintains Narwhals LazyFrame."""
        import narwhals as nw

        strategy = DataFrameSelectFactory.get_strategy(sample_narwhals_lazyframe)

        # Chain: select -> head
        selected = strategy.select(sample_narwhals_lazyframe, ["id", "name"])
        result = strategy.head(selected, 3)

        # Verify both remain lazy
        check.is_true(hasattr(nw.to_native(selected), 'collect'), "After select should be lazy")
        check.is_true(hasattr(nw.to_native(result), 'collect'), "After head should be lazy")


@pytest.mark.unit
@pytest.mark.parametrize("backend_fixture", BATCHING_BACKEND_FIXTURES)
class TestSplitBatchesGenerator:
    """Test split_in_batches_generator() functionality across all backends."""

    def test_generator_basic(self, backend_fixture, request):
        """Test basic generator functionality."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches = []
        for batch in strategy.split_in_batches_generator(df, batch_size=25):
            batches.append(batch)

        # Should have 4 batches (100 rows / 25 per batch)
        check.equal(len(batches), 4, f"Should have 4 batches for {backend_fixture}")

        # Verify each batch size
        for i, batch in enumerate(batches):
            # Get strategy for the batch (may be different from source df strategy)
            batch_strategy = DataFrameSelectFactory.get_strategy(batch)
            batch_count = batch_strategy.count(batch)
            check.equal(batch_count, 25, f"Batch {i} should have 25 rows for {backend_fixture}")

    def test_generator_early_termination(self, backend_fixture, request):
        """Test generator can be terminated early without processing all batches."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches = []
        for i, batch in enumerate(strategy.split_in_batches_generator(df, batch_size=10)):
            batches.append(batch)
            if i >= 2:  # Get first 3 batches (0, 1, 2)
                break

        check.equal(len(batches), 3, msg=f"Should only have 3 batches due to early termination for {backend_fixture}")

        # Verify first 3 batches have correct size
        for i, batch in enumerate(batches):
            batch_strategy = DataFrameSelectFactory.get_strategy(batch)
            batch_count = batch_strategy.count(batch)
            check.equal(batch_count, 10, f"Batch {i} should have 10 rows for {backend_fixture}")

    def test_generator_vs_list_equivalence(self, backend_fixture, request):
        """Test that generator and list methods produce equivalent results."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batch_size = 25

        # Get batches via list method
        batches_list, total = strategy.split_in_batches(df, batch_size=batch_size)

        # Get batches via generator method
        batches_gen = list(strategy.split_in_batches_generator(df, batch_size=batch_size))

        # Should have same number of batches
        check.equal(len(batches_gen), len(batches_list), f"Generator and list should produce same number of batches for {backend_fixture}")

        # Each batch should have same size
        for i, (batch_gen, batch_list) in enumerate(zip(batches_gen, batches_list)):
            gen_count = DataFrameSelectFactory.get_strategy(batch_gen).count(batch_gen)
            list_count = DataFrameSelectFactory.get_strategy(batch_list).count(batch_list)
            check.equal(gen_count, list_count, f"Batch {i} counts should match for {backend_fixture}")

    def test_generator_with_remainder(self, backend_fixture, request):
        """Test generator with batch_size that doesn't evenly divide row count."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches = list(strategy.split_in_batches_generator(df, batch_size=30))

        # Should have 4 batches (3 full + 1 partial)
        check.equal(len(batches), 4, f"Should have 4 batches for {backend_fixture}")

        # First 3 batches should have 30 rows
        for i in range(3):
            batch_strategy_i = DataFrameSelectFactory.get_strategy(batches[i])
            batch_count = batch_strategy_i.count(batches[i])
            check.equal(batch_count, 30, f"Batch {i} should have 30 rows for {backend_fixture}")

        # Last batch should have 10 rows (100 - 90)
        last_batch_strategy = DataFrameSelectFactory.get_strategy(batches[-1])
        last_batch_count = last_batch_strategy.count(batches[-1])
        check.equal(last_batch_count, 10, f"Last batch should have 10 rows for {backend_fixture}")

    def test_generator_larger_than_df(self, backend_fixture, request):
        """Test generator when batch_size > DataFrame size."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches = list(strategy.split_in_batches_generator(df, batch_size=200))

        # Should have 1 batch containing all rows
        check.equal(len(batches), 1, f"Should have 1 batch for {backend_fixture}")
        batch_strategy = DataFrameSelectFactory.get_strategy(batches[0])
        check.equal(batch_strategy.count(batches[0]), 100, f"Batch should have 100 rows for {backend_fixture}")

    def test_generator_preserves_columns(self, backend_fixture, request):
        """Test that generator batches preserve all columns."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        original_columns = strategy.column_names(df)

        for i, batch in enumerate(strategy.split_in_batches_generator(df, batch_size=25)):
            batch_columns = strategy.column_names(batch)
            check.equal(
                sorted(batch_columns),
                sorted(original_columns),
                f"Batch {i} columns should match original for {backend_fixture}"
            )

    def test_generator_invalid_size(self, backend_fixture, request):
        """Test that generator with batch_size <= 0 raises ValueError."""
        df = request.getfixturevalue(backend_fixture)
        strategy = DataFrameSelectFactory.get_strategy(df)

        with pytest.raises(ValueError, match="greater than 0"):
            list(strategy.split_in_batches_generator(df, batch_size=0))

        with pytest.raises(ValueError, match="greater than 0"):
            list(strategy.split_in_batches_generator(df, batch_size=-10))


@pytest.mark.unit
class TestGeneratorLazyFrameBehavior:
    """Test lazy frame specific behavior for split_in_batches_generator()."""

    def test_polars_lazyframe_generator_preserves_lazy(self, large_polars_lazyframe_for_batching):
        """Test that Polars LazyFrame generator yields lazy batches."""
        import polars as pl

        df = large_polars_lazyframe_for_batching
        strategy = DataFrameSelectFactory.get_strategy(df)

        # Get first batch from generator
        gen = strategy.split_in_batches_generator(df, batch_size=25)
        first_batch = next(gen)

        # Generator should preserve laziness (unlike list method)
        check.is_instance(first_batch, pl.LazyFrame, "Generator batch should be LazyFrame")

    def test_narwhals_lazyframe_generator_preserves_lazy(self, large_narwhals_lazyframe_for_batching):
        """Test that Narwhals LazyFrame generator yields lazy batches."""
        import narwhals as nw

        df = large_narwhals_lazyframe_for_batching
        strategy = DataFrameSelectFactory.get_strategy(df)

        # Get first batch from generator
        gen = strategy.split_in_batches_generator(df, batch_size=25)
        first_batch = next(gen)

        # Generator should preserve laziness
        native_batch = nw.to_native(first_batch)
        check.is_true(
            hasattr(native_batch, 'collect'),
            "Generator batch should be lazy (have collect method)"
        )

    def test_polars_lazyframe_generator_correctness(self, large_polars_lazyframe_for_batching):
        """Test that Polars LazyFrame generator batches have correct sizes."""
        df = large_polars_lazyframe_for_batching
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches = list(strategy.split_in_batches_generator(df, batch_size=25))

        # Should have 4 batches
        check.equal(len(batches), 4, "Should have 4 batches")

        # Each batch should have 25 rows when collected
        for i, batch in enumerate(batches):
            batch_strategy = DataFrameSelectFactory.get_strategy(batch)
            batch_count = batch_strategy.count(batch)
            check.equal(batch_count, 25, f"Batch {i} should have 25 rows")

    def test_narwhals_lazyframe_generator_correctness(self, large_narwhals_lazyframe_for_batching):
        """Test that Narwhals LazyFrame generator batches have correct sizes."""
        df = large_narwhals_lazyframe_for_batching
        strategy = DataFrameSelectFactory.get_strategy(df)

        batches = list(strategy.split_in_batches_generator(df, batch_size=25))

        # Should have 4 batches
        check.equal(len(batches), 4, "Should have 4 batches")

        # Each batch should have 25 rows when collected
        for i, batch in enumerate(batches):
            batch_strategy = DataFrameSelectFactory.get_strategy(batch)
            batch_count = batch_strategy.count(batch)
            check.equal(batch_count, 25, f"Batch {i} should have 25 rows")
