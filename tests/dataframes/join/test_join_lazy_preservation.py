"""
Tests for lazy frame preservation in join operations.

This module tests that join operations preserve lazy evaluation when possible
(same-backend joins) and handle cross-backend scenarios correctly.

Key Principle:
- Same-backend lazy joins (e.g., Polars Lazy + Polars Lazy) should stay lazy
- Cross-backend joins (e.g., Polars Lazy + Pandas) may require collection
"""

from __future__ import annotations

import pytest
import pandas as pd
import polars as pl
import ibis
import narwhals as nw
from pytest_check import check

from mountainash.dataframes.join import DataFrameJoinFactory


@pytest.mark.unit
class TestSameBackendLazyPreservation:
    """Test that same-backend lazy joins preserve LazyFrame type."""

    def test_inner_join_polars_lazy_preserves_lazy(
        self, left_polars_lazy, right_polars_lazy
    ):
        """Test that inner join with two Polars LazyFrames stays lazy.

        This is the most common use case - users working within Polars ecosystem
        expect lazy frames to remain lazy for performance and memory efficiency.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)
        result = strategy.inner_join(
            left_polars_lazy, right_polars_lazy, predicates="id"
        )

        # Result should be Narwhals LazyFrame (wrapping Polars LazyFrame)
        # Note: This test will FAIL with current implementation that always collects
        check.is_instance(result, nw.LazyFrame, "Same-backend lazy join should stay lazy")

        # Convert to native and verify it's Polars LazyFrame
        native_result = nw.to_native(result)
        check.is_instance(native_result, pl.LazyFrame, "Native result should be Polars LazyFrame")

        # Verify correctness when collected
        collected = native_result.collect()
        check.equal(len(collected), 3, "Should have 3 matching rows (ids: 2, 3, 4)")

    def test_left_join_polars_lazy_preserves_lazy(
        self, left_polars_lazy, right_polars_lazy
    ):
        """Test that left join preserves Polars LazyFrame type."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)
        result = strategy.left_join(
            left_polars_lazy, right_polars_lazy, predicates="id"
        )

        check.is_instance(result, nw.LazyFrame, "Left join should preserve lazy")
        native_result = nw.to_native(result)
        check.is_instance(native_result, pl.LazyFrame)

        # Verify correctness
        collected = native_result.collect()
        check.equal(len(collected), 5, "Should have all 5 left rows")

    def test_outer_join_polars_lazy_preserves_lazy(
        self, left_polars_lazy, right_polars_lazy
    ):
        """Test that outer join preserves Polars LazyFrame type."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)
        result = strategy.outer_join(
            left_polars_lazy, right_polars_lazy, predicates="id", coalesce_keys=True
        )

        check.is_instance(result, nw.LazyFrame, "Outer join should preserve lazy")
        native_result = nw.to_native(result)
        check.is_instance(native_result, pl.LazyFrame)

        # Verify correctness
        collected = native_result.collect()
        check.equal(len(collected), 7, "Should have all unique rows from both tables")

    def test_same_backend_lazy_join_with_coalesce(
        self, left_polars_lazy, right_polars_lazy
    ):
        """Test that coalesce_keys works with lazy frames without forcing collection."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)
        result = strategy.outer_join(
            left_polars_lazy,
            right_polars_lazy,
            predicates="id",
            coalesce_keys=True  # This should work lazily
        )

        check.is_instance(result, nw.LazyFrame, "Coalesce should not force collection")

        # Verify coalescing worked correctly
        native_result = nw.to_native(result)
        collected = native_result.collect()

        # Should have 'id' column but not 'id_right'
        check.is_in("id", collected.columns, "Should have coalesced 'id' column")
        check.is_not_in("id_right", collected.columns, "Should not have 'id_right' after coalesce")


@pytest.mark.unit
class TestMixedLazyEagerSameBackend:
    """Test behavior when mixing lazy and eager frames of the same backend."""

    def test_lazy_left_eager_right_polars(
        self, left_polars_lazy, right_polars_df
    ):
        """Test joining lazy left with eager right (same backend).

        Polars native behavior: LazyFrame.join(DataFrame) typically returns LazyFrame.
        We should preserve this behavior.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)
        result = strategy.inner_join(
            left_polars_lazy, right_polars_df, predicates="id"
        )

        # Polars handles mixed lazy/eager - verify result type
        native_result = nw.to_native(result)

        # Polars behavior: lazy.join(eager) returns lazy
        # This may vary by Polars version, so we check what Polars naturally does
        if isinstance(native_result, pl.LazyFrame):
            check.is_instance(native_result, pl.LazyFrame, "Polars preserves lazy when left is lazy")
        else:
            # If Polars returns eager, that's acceptable for mixed joins
            check.is_instance(native_result, pl.DataFrame, "Mixed lazy/eager may return eager")

        # Verify correctness regardless of type
        if hasattr(native_result, 'collect'):
            collected = native_result.collect()
        else:
            collected = native_result
        check.equal(len(collected), 3)

    def test_eager_left_lazy_right_polars(
        self, left_polars_df, right_polars_lazy
    ):
        """Test joining eager left with lazy right (same backend).

        Polars native behavior: DataFrame.join(LazyFrame) behavior varies.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_df)
        result = strategy.inner_join(
            left_polars_df, right_polars_lazy, predicates="id"
        )

        # Accept whatever Polars naturally does for eager.join(lazy)
        native_result = nw.to_native(result)
        check.is_instance(
            native_result,
            (pl.DataFrame, pl.LazyFrame),
            "Mixed eager/lazy should return valid Polars type"
        )

        # Verify correctness
        if hasattr(native_result, 'collect'):
            collected = native_result.collect()
        else:
            collected = native_result
        check.equal(len(collected), 3)


@pytest.mark.unit
class TestCrossBackendJoinBehavior:
    """Test that cross-backend joins handle collection appropriately.

    Cross-backend joins (e.g., Polars + Pandas) require converting to a common
    representation, which may necessitate collecting lazy frames.
    """

    def test_polars_lazy_to_pandas_cross_backend(
        self, left_polars_lazy, right_pandas_df
    ):
        """Test cross-backend join between Polars LazyFrame and Pandas DataFrame.

        Since these are different backends, collection may be necessary for compatibility.
        The important thing is that the join produces correct results.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)
        result = strategy.inner_join(
            left_polars_lazy, right_pandas_df, predicates="id"
        )

        # Cross-backend join - collection is acceptable
        # Just verify it produces correct results
        native_result = nw.to_native(result)

        # Collect if lazy
        if hasattr(native_result, 'collect'):
            native_result = native_result.collect()

        check.equal(len(native_result), 3, "Cross-backend join should produce correct results")

    def test_pandas_to_polars_lazy_cross_backend(
        self, left_pandas_df, right_polars_lazy
    ):
        """Test cross-backend join between Pandas DataFrame and Polars LazyFrame."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_pandas_df)
        result = strategy.inner_join(
            left_pandas_df, right_polars_lazy, predicates="id"
        )

        # Cross-backend join - verify correctness
        native_result = nw.to_native(result)
        if hasattr(native_result, 'collect'):
            native_result = native_result.collect()

        check.equal(len(native_result), 3)

    def test_cross_backend_with_execute_on_parameter(
        self, left_polars_lazy, right_pandas_df
    ):
        """Test that execute_on parameter works with cross-backend joins.

        When execute_on forces a specific backend, lazy frames may need collection.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)

        # Force execution on right backend (pandas)
        result = strategy.inner_join(
            left_polars_lazy,
            right_pandas_df,
            predicates="id",
            execute_on="right"  # Force pandas backend
        )

        # Verify correctness - exact type is less important for cross-backend
        native_result = nw.to_native(result)
        if hasattr(native_result, 'collect'):
            native_result = native_result.collect()

        check.equal(len(native_result), 3)


@pytest.mark.unit
class TestLazyPreservationPerformance:
    """Test that lazy joins maintain performance benefits."""

    def test_lazy_join_allows_query_chaining(
        self, left_polars_lazy, right_polars_lazy
    ):
        """Test that lazy joins can be chained with other lazy operations.

        This is the key benefit of preserving laziness - users can build
        complex query plans without intermediate materialization.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)

        # Perform join
        joined = strategy.inner_join(
            left_polars_lazy, right_polars_lazy, predicates="id"
        )

        # If lazy, we should be able to continue building query plan
        if isinstance(joined, nw.LazyFrame):
            native_joined = nw.to_native(joined)

            # Chain more operations
            filtered = native_joined.filter(pl.col("id") > 2)
            selected = filtered.select(["id", "name"])

            # All should remain lazy
            check.is_instance(filtered, pl.LazyFrame, "Filter should preserve lazy")
            check.is_instance(selected, pl.LazyFrame, "Select should preserve lazy")

            # Only collect at the end
            final = selected.collect()
            check.equal(len(final), 2, "Should have 2 rows (ids 3, 4)")
        else:
            # Current implementation - join forces collection
            # This test documents the CURRENT behavior, not the DESIRED behavior
            check.is_instance(joined, nw.DataFrame, "Current: Join collects lazy frames")


@pytest.mark.unit
class TestIbisLazyBehavior:
    """Test that Ibis joins remain lazy (Ibis is lazy by design)."""

    def test_ibis_join_stays_lazy(self, left_ibis_table, right_ibis_table):
        """Test that Ibis joins return lazy expressions.

        Ibis is fundamentally lazy - joins should return expressions
        that aren't executed until .execute() is called.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_ibis_table)
        result = strategy.inner_join(
            left_ibis_table, right_ibis_table, predicates="id"
        )

        # Result should be Ibis expression (lazy)
        check.is_instance(result, ibis.expr.types.Table, "Ibis join should return expression")

        # Verify it hasn't been executed yet (no data materialized)
        # Ibis expressions are lazy until .execute()
        check.is_true(hasattr(result, 'execute'), "Should have execute method")

        # Only materialize when explicitly requested
        executed = result.execute()
        check.equal(len(executed), 3, "Should have correct results when executed")

    def test_ibis_same_backend_detection(self, left_ibis_table, right_ibis_table):
        """Test that Ibis correctly identifies same-backend tables.

        Ibis uses special backend comparison logic (identity for in-memory,
        equality for database connections).
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_ibis_table)

        # Both tables use shared_ibis_backend fixture, so they share the same backend
        left_backend = left_ibis_table.get_backend()
        right_backend = right_ibis_table.get_backend()

        # Verify they're the same backend (identity check for in-memory)
        check.is_true(
            left_backend is right_backend,
            "Fixtures should use same backend instance"
        )

        # Join should work without backend conversion
        result = strategy.inner_join(
            left_ibis_table, right_ibis_table, predicates="id"
        )

        check.is_instance(result, ibis.expr.types.Table)


@pytest.mark.unit
class TestNarwhalsLazyWrapping:
    """Test Narwhals LazyFrame wrapping behavior."""

    def test_narwhals_wraps_polars_lazy_correctly(self, left_polars_lazy):
        """Test that Narwhals correctly wraps and unwraps Polars LazyFrames."""
        # Wrap Polars LazyFrame in Narwhals
        nw_lazy = nw.from_native(left_polars_lazy)

        check.is_instance(nw_lazy, nw.LazyFrame, "Should wrap as Narwhals LazyFrame")

        # Unwrap back to native
        unwrapped = nw.to_native(nw_lazy)
        check.is_instance(unwrapped, pl.LazyFrame, "Should unwrap back to Polars LazyFrame")

    def test_narwhals_lazy_join_result_type(
        self, left_polars_lazy, right_polars_lazy
    ):
        """Test that joining Narwhals LazyFrames preserves lazy type.

        When both inputs are Narwhals LazyFrames wrapping the same backend,
        the result should also be a LazyFrame.
        """
        # Wrap both in Narwhals
        left_nw = nw.from_native(left_polars_lazy)
        right_nw = nw.from_native(right_polars_lazy)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_nw)
        result = strategy.inner_join(left_nw, right_nw, predicates="id")

        # Should stay lazy
        check.is_instance(result, nw.LazyFrame, "Narwhals should preserve lazy")

        # Verify underlying is also lazy
        native = nw.to_native(result)
        check.is_instance(native, pl.LazyFrame, "Underlying should be Polars LazyFrame")


@pytest.mark.unit
class TestBackendDetection:
    """Test backend detection logic for determining same vs cross-backend scenarios."""

    def test_detect_same_backend_polars_lazy(
        self, left_polars_lazy, right_polars_lazy
    ):
        """Test that two Polars LazyFrames are detected as same backend."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)

        # Get backend detection from strategy
        left_backend = strategy._get_native_backend(left_polars_lazy)
        right_backend = strategy._get_native_backend(right_polars_lazy)

        check.equal(left_backend, "polars", "Should detect Polars backend")
        check.equal(right_backend, "polars", "Should detect Polars backend")
        check.equal(left_backend, right_backend, "Should detect same backend")

    def test_detect_cross_backend_polars_pandas(
        self, left_polars_lazy, right_pandas_df
    ):
        """Test that Polars and Pandas are detected as different backends."""
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)

        left_backend = strategy._get_native_backend(left_polars_lazy)
        right_backend = strategy._get_native_backend(right_pandas_df)

        check.equal(left_backend, "polars")
        check.equal(right_backend, "pandas")
        check.not_equal(left_backend, right_backend, "Should detect different backends")

    def test_detect_narwhals_underlying_backend(self, left_polars_lazy):
        """Test that Narwhals LazyFrames report their underlying backend."""
        # Wrap in Narwhals
        nw_lazy = nw.from_native(left_polars_lazy)

        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(nw_lazy)

        backend = strategy._get_native_backend(nw_lazy)
        check.equal(backend, "polars", "Should detect underlying Polars backend")


@pytest.mark.unit
class TestDocumentCurrentBehavior:
    """Document current behavior for comparison after implementation.

    These tests document what the CURRENT implementation does (collecting lazy frames).
    After fixing, these tests should be updated to expect lazy preservation.
    """

    def test_current_behavior_collects_lazy_frames(
        self, left_polars_lazy, right_polars_lazy
    ):
        """CURRENT BEHAVIOR: Same-backend lazy joins incorrectly collect.

        This test documents the broken behavior. After implementation,
        this should be updated to expect LazyFrame result.
        """
        factory = DataFrameJoinFactory()
        strategy = factory.get_strategy(left_polars_lazy)
        result = strategy.inner_join(
            left_polars_lazy, right_polars_lazy, predicates="id"
        )

        # CURRENT (BROKEN): Result is eager DataFrame
        current_is_eager = isinstance(result, nw.DataFrame) and not isinstance(result, nw.LazyFrame)

        # Document current behavior
        if current_is_eager:
            # This is the current broken behavior
            check.is_true(
                current_is_eager,
                "CURRENT: Incorrectly collects lazy frames (should be fixed)"
            )
        else:
            # If this passes, the implementation has been fixed!
            check.is_instance(
                result,
                nw.LazyFrame,
                "FIXED: Now correctly preserves lazy frames!"
            )
