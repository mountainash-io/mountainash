"""
Tests for LazyFrame-specific cast operations.

This module tests casting operations involving Polars LazyFrames and Narwhals LazyFrames,
ensuring proper lazy evaluation, collection behavior, and the as_lazy parameter.
"""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import narwhals as nw

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.cast import DataFrameCastFactory
from mountainash.dataframes.cast.cast_from_polars_lazyframe import CastFromPolarsLazyFrame
from mountainash.dataframes.cast.cast_from_narwhals_lazyframe import CastFromNarwhalsLazyFrame


# ============================================================================
# LAZYFRAME FIXTURES
# ============================================================================

@pytest.fixture
def sample_data():
    """Sample data for LazyFrame tests."""
    return {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "category": ["A", "B", "A", "C", "B"]
    }


@pytest.fixture
def polars_lazyframe(sample_data):
    """Polars LazyFrame fixture."""
    return pl.DataFrame(sample_data).lazy()


@pytest.fixture
def narwhals_lazyframe(sample_data):
    """Narwhals LazyFrame fixture."""
    polars_df = pl.DataFrame(sample_data)
    return nw.from_native(polars_df.lazy())


@pytest.fixture
def polars_dataframe(sample_data):
    """Polars eager DataFrame fixture."""
    return pl.DataFrame(sample_data)


@pytest.fixture
def pandas_dataframe(sample_data):
    """Pandas DataFrame fixture."""
    return pd.DataFrame(sample_data)


# ============================================================================
# POLARS LAZYFRAME STRATEGY TESTS
# ============================================================================

@pytest.mark.unit
class TestPolarsLazyFrameStrategy:
    """Test CastFromPolarsLazyFrame strategy."""

    def test_strategy_selection_polars_lazy(self, polars_lazyframe):
        """Test that factory selects correct strategy for Polars LazyFrame."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_lazyframe)

        assert strategy == CastFromPolarsLazyFrame

    def test_polars_lazy_to_pandas_collects(self, polars_lazyframe):
        """Test Polars LazyFrame to pandas collects automatically."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_pandas(polars_lazyframe)

        # Should be materialized pandas DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert list(result.columns) == ["id", "name", "value", "category"]

    def test_polars_lazy_to_polars_default_preserves_lazy(self, polars_lazyframe):
        """Test Polars LazyFrame to polars preserves laziness by default."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_polars(polars_lazyframe)

        # Default (as_lazy=None) should preserve input type (lazy)
        assert isinstance(result, pl.LazyFrame)

        # Verify correctness when collected
        collected = result.collect()
        assert len(collected) == 5

    def test_polars_lazy_to_polars_with_lazy_flag(self, polars_lazyframe):
        """Test Polars LazyFrame to polars with as_lazy=True."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_polars(polars_lazyframe, as_lazy=True)

        # Should remain lazy
        assert isinstance(result, pl.LazyFrame)

    def test_polars_lazy_to_polars_with_eager_flag(self, polars_lazyframe):
        """Test Polars LazyFrame to polars with as_lazy=False."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_polars(polars_lazyframe, as_lazy=False)

        # Should be collected
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 5

    def test_polars_lazy_to_pyarrow_collects(self, polars_lazyframe):
        """Test Polars LazyFrame to pyarrow collects automatically."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_pyarrow(polars_lazyframe)

        # Should be materialized PyArrow Table
        assert isinstance(result, pa.Table)
        assert len(result) == 5

    def test_polars_lazy_to_narwhals(self, polars_lazyframe):
        """Test Polars LazyFrame to narwhals conversion preserves laziness."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_narwhals(polars_lazyframe)

        # Default (as_lazy=None) should preserve input type (lazy)
        assert isinstance(result, nw.LazyFrame)

        # Verify correctness when collected
        collected = nw.to_native(result).collect()
        assert len(collected) == 5

    def test_polars_lazy_to_dict_collects(self, polars_lazyframe):
        """Test Polars LazyFrame to dict collects automatically."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_dictionary_of_lists(polars_lazyframe)

        # Should be materialized dictionary
        assert isinstance(result, dict)
        assert set(result.keys()) == {"id", "name", "value", "category"}
        assert all(isinstance(v, list) for v in result.values())

    def test_polars_lazy_to_list_of_dicts_collects(self, polars_lazyframe):
        """Test Polars LazyFrame to list of dicts collects automatically."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_list_of_dictionaries(polars_lazyframe)

        # Should be materialized list
        assert isinstance(result, list)
        assert len(result) == 5
        assert all(isinstance(item, dict) for item in result)

    def test_polars_lazy_to_ibis(self, polars_lazyframe):
        """Test Polars LazyFrame to Ibis conversion."""
        strategy = CastFromPolarsLazyFrame

        result = strategy.to_ibis(polars_lazyframe)

        # Should create Ibis table
        assert result is not None
        assert hasattr(result, 'columns')


@pytest.mark.unit
class TestNarwhalsLazyFrameStrategy:
    """Test CastFromNarwhalsLazyFrame strategy."""

    def test_strategy_selection_narwhals_lazy(self, narwhals_lazyframe):
        """Test that factory selects correct strategy for Narwhals LazyFrame."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(narwhals_lazyframe)

        assert strategy == CastFromNarwhalsLazyFrame

    def test_narwhals_lazy_to_pandas(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame to pandas."""
        strategy = CastFromNarwhalsLazyFrame

        result = strategy.to_pandas(narwhals_lazyframe)

        # Should be materialized pandas DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    def test_narwhals_lazy_to_polars(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame to polars."""
        strategy = CastFromNarwhalsLazyFrame

        result = strategy.to_polars(narwhals_lazyframe)

        # Should be polars type
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))

    def test_narwhals_lazy_to_polars_with_lazy_flag(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame to polars with as_lazy=True."""
        strategy = CastFromNarwhalsLazyFrame

        result = strategy.to_polars(narwhals_lazyframe, as_lazy=True)

        # Should be lazy if possible
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))

    def test_narwhals_lazy_to_pyarrow(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame to pyarrow."""
        strategy = CastFromNarwhalsLazyFrame

        result = strategy.to_pyarrow(narwhals_lazyframe)

        # Should be materialized PyArrow Table
        assert isinstance(result, pa.Table)
        assert len(result) == 5

    def test_narwhals_lazy_to_narwhals(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame to narwhals preserves laziness."""
        strategy = CastFromNarwhalsLazyFrame

        result = strategy.to_narwhals(narwhals_lazyframe)

        # Default (as_lazy=None) should preserve input type (lazy)
        assert isinstance(result, nw.LazyFrame)

        # Verify correctness when collected
        collected = result.collect()
        assert len(collected) == 5

    def test_narwhals_lazy_to_dict(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame to dict."""
        strategy = CastFromNarwhalsLazyFrame

        result = strategy.to_dictionary_of_lists(narwhals_lazyframe)

        # Should be materialized dictionary
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_narwhals_lazy_to_list_of_dicts(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame to list of dicts."""
        strategy = CastFromNarwhalsLazyFrame

        result = strategy.to_list_of_dictionaries(narwhals_lazyframe)

        # Should be materialized list
        assert isinstance(result, list)
        assert len(result) == 5

    def test_narwhals_lazy_to_ibis(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame to Ibis."""
        strategy = CastFromNarwhalsLazyFrame

        result = strategy.to_ibis(narwhals_lazyframe)

        # Should create Ibis table
        assert result is not None
        assert hasattr(result, 'columns')


# ============================================================================
# LAZY EVALUATION BEHAVIOR TESTS
# ============================================================================

@pytest.mark.unit
class TestLazyEvaluationBehavior:
    """Test lazy evaluation characteristics and timing."""

    def test_polars_lazy_operations_remain_lazy(self, polars_lazyframe):
        """Test that operations on Polars LazyFrame remain lazy."""
        # Apply filter (should remain lazy)
        filtered = polars_lazyframe.filter(pl.col("id") > 2)

        # Should still be lazy
        assert isinstance(filtered, pl.LazyFrame)

        # Convert to pandas should collect
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(filtered)
        result = strategy.to_pandas(filtered)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3  # IDs 3, 4, 5

    def test_polars_lazy_collect_only_when_needed(self, polars_lazyframe):
        """Test that Polars LazyFrame only collects when necessary."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_lazyframe)

        # to_polars with as_lazy=True should not collect
        result_lazy = strategy.to_polars(polars_lazyframe, as_lazy=True)
        assert isinstance(result_lazy, pl.LazyFrame)

        # to_pandas should collect
        result_pandas = strategy.to_pandas(polars_lazyframe)
        assert isinstance(result_pandas, pd.DataFrame)

    def test_narwhals_lazy_preserves_lazy_when_possible(self, narwhals_lazyframe):
        """Test that Narwhals LazyFrame preserves laziness when possible."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(narwhals_lazyframe)

        # to_narwhals should preserve lazy nature by default
        result = strategy.to_narwhals(narwhals_lazyframe)
        assert isinstance(result, nw.LazyFrame)

        # Verify correctness when collected
        collected = result.collect()
        assert len(collected) == 5


# ============================================================================
# CONVERSION TO LAZYFRAME TESTS
# ============================================================================

@pytest.mark.unit
class TestConversionToLazyFrame:
    """Test converting eager DataFrames to LazyFrames."""

    def test_pandas_to_polars_lazy(self, pandas_dataframe):
        """Test pandas to Polars LazyFrame conversion."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_dataframe)

        result = strategy.to_polars(pandas_dataframe, as_lazy=True)

        # Should be LazyFrame
        assert isinstance(result, pl.LazyFrame)

    def test_polars_eager_to_polars_lazy(self, polars_dataframe):
        """Test Polars eager to Polars LazyFrame conversion."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_dataframe)

        result = strategy.to_polars(polars_dataframe, as_lazy=True)

        # Should be LazyFrame
        assert isinstance(result, pl.LazyFrame)

    def test_pyarrow_to_polars_lazy(self, sample_data):
        """Test PyArrow to Polars LazyFrame conversion."""
        pyarrow_table = pa.table(sample_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pyarrow_table)

        result = strategy.to_polars(pyarrow_table, as_lazy=True)

        # Should be LazyFrame
        assert isinstance(result, pl.LazyFrame)

    def test_ibis_to_polars_lazy(self, sample_data):
        """Test Ibis to Polars LazyFrame conversion."""
        ibis_table = DataFrameUtils.create_ibis(sample_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table)

        result = strategy.to_polars(ibis_table, as_lazy=True)

        # Should be LazyFrame
        assert isinstance(result, pl.LazyFrame)


# ============================================================================
# ROUNDTRIP TESTS WITH LAZY FRAMES
# ============================================================================

@pytest.mark.unit
class TestLazyFrameRoundtrips:
    """Test data integrity in roundtrip conversions involving LazyFrames."""

    def test_polars_lazy_to_pandas_to_polars_lazy(self, polars_lazyframe):
        """Test Polars LazyFrame -> pandas -> Polars LazyFrame roundtrip."""
        factory = DataFrameCastFactory()

        # Lazy -> pandas
        lazy_strategy = factory.get_strategy(polars_lazyframe)
        pandas_result = lazy_strategy.to_pandas(polars_lazyframe)

        # pandas -> Lazy
        pandas_strategy = factory.get_strategy(pandas_result)
        lazy_result = pandas_strategy.to_polars(pandas_result, as_lazy=True)

        # Verify
        assert isinstance(lazy_result, pl.LazyFrame)
        collected = lazy_result.collect()
        assert len(collected) == 5
        assert set(collected.columns) == {"id", "name", "value", "category"}

    def test_polars_lazy_to_pyarrow_to_polars_lazy(self, polars_lazyframe):
        """Test Polars LazyFrame -> PyArrow -> Polars LazyFrame roundtrip."""
        factory = DataFrameCastFactory()

        # Lazy -> PyArrow
        lazy_strategy = factory.get_strategy(polars_lazyframe)
        pyarrow_result = lazy_strategy.to_pyarrow(polars_lazyframe)

        # PyArrow -> Lazy
        pyarrow_strategy = factory.get_strategy(pyarrow_result)
        lazy_result = pyarrow_strategy.to_polars(pyarrow_result, as_lazy=True)

        # Verify
        assert isinstance(lazy_result, pl.LazyFrame)
        collected = lazy_result.collect()
        assert len(collected) == 5

    def test_narwhals_lazy_to_pandas_to_narwhals(self, narwhals_lazyframe):
        """Test Narwhals LazyFrame -> pandas -> Narwhals roundtrip."""
        factory = DataFrameCastFactory()

        # Lazy -> pandas
        lazy_strategy = factory.get_strategy(narwhals_lazyframe)
        pandas_result = lazy_strategy.to_pandas(narwhals_lazyframe)

        # pandas -> Narwhals
        pandas_strategy = factory.get_strategy(pandas_result)
        narwhals_result = pandas_strategy.to_narwhals(pandas_result)

        # Verify
        assert isinstance(narwhals_result, nw.DataFrame)
        assert len(narwhals_result) == 5

    def test_eager_to_lazy_to_eager_preserves_data(self, polars_dataframe):
        """Test eager -> lazy -> eager preserves data."""
        factory = DataFrameCastFactory()

        # Eager -> Lazy
        eager_strategy = factory.get_strategy(polars_dataframe)
        lazy_result = eager_strategy.to_polars(polars_dataframe, as_lazy=True)

        # Lazy -> Eager
        lazy_strategy = factory.get_strategy(lazy_result)
        eager_result = lazy_strategy.to_polars(lazy_result, as_lazy=False)

        # Compare
        assert isinstance(eager_result, pl.DataFrame)
        assert len(eager_result) == len(polars_dataframe)
        assert eager_result.columns == polars_dataframe.columns
        # Sort both for comparison
        assert eager_result.sort("id").equals(polars_dataframe.sort("id"))


# ============================================================================
# EDGE CASES WITH LAZY FRAMES
# ============================================================================

@pytest.mark.unit
class TestLazyFrameEdgeCases:
    """Test edge cases specific to LazyFrames."""

    def test_empty_polars_lazy_to_pandas(self):
        """Test empty Polars LazyFrame to pandas."""
        empty_lazy = pl.DataFrame({}).lazy()
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(empty_lazy)

        result = strategy.to_pandas(empty_lazy)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_single_row_polars_lazy_to_pandas(self):
        """Test single-row Polars LazyFrame to pandas."""
        data = {"id": [1], "name": ["Alice"]}
        lazy_df = pl.DataFrame(data).lazy()
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(lazy_df)

        result = strategy.to_pandas(lazy_df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    def test_single_column_polars_lazy_to_pandas(self):
        """Test single-column Polars LazyFrame to pandas."""
        data = {"id": [1, 2, 3]}
        lazy_df = pl.DataFrame(data).lazy()
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(lazy_df)

        result = strategy.to_pandas(lazy_df)

        assert isinstance(result, pd.DataFrame)
        assert len(result.columns) == 1

    def test_polars_lazy_with_nulls_to_pandas(self):
        """Test Polars LazyFrame with nulls to pandas."""
        data = {
            "id": [1, 2, None, 4],
            "name": ["Alice", None, "Charlie", "Diana"]
        }
        lazy_df = pl.DataFrame(data).lazy()
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(lazy_df)

        result = strategy.to_pandas(lazy_df)

        assert isinstance(result, pd.DataFrame)
        assert result['name'].isna().sum() > 0

    def test_large_polars_lazy_to_pandas(self):
        """Test large Polars LazyFrame to pandas (1000 rows)."""
        data = {
            "id": list(range(1000)),
            "value": [i * 10.5 for i in range(1000)]
        }
        lazy_df = pl.DataFrame(data).lazy()
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(lazy_df)

        result = strategy.to_pandas(lazy_df)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1000


# ============================================================================
# AS_LAZY PARAMETER TESTS
# ============================================================================

@pytest.mark.unit
class TestAsLazyParameter:
    """Test the as_lazy parameter across all strategies."""

    @pytest.mark.parametrize("source_type,fixture_name", [
        ("pandas", "pandas_dataframe"),
        ("polars_eager", "polars_dataframe"),
        ("polars_lazy", "polars_lazyframe"),
    ])
    def test_as_lazy_true_produces_lazyframe(self, request, source_type, fixture_name):
        """Test as_lazy=True produces LazyFrame."""
        source_df = request.getfixturevalue(fixture_name)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(source_df)

        result = strategy.to_polars(source_df, as_lazy=True)

        assert isinstance(result, pl.LazyFrame), \
            f"{source_type} with as_lazy=True should produce LazyFrame"

    @pytest.mark.parametrize("source_type,fixture_name", [
        ("pandas", "pandas_dataframe"),
        ("polars_eager", "polars_dataframe"),
        ("polars_lazy", "polars_lazyframe"),
    ])
    def test_as_lazy_false_produces_dataframe(self, request, source_type, fixture_name):
        """Test as_lazy=False produces eager DataFrame."""
        source_df = request.getfixturevalue(fixture_name)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(source_df)

        result = strategy.to_polars(source_df, as_lazy=False)

        assert isinstance(result, pl.DataFrame), \
            f"{source_type} with as_lazy=False should produce DataFrame"

    def test_as_lazy_default_behavior(self, pandas_dataframe):
        """Test default behavior when as_lazy is not specified."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_dataframe)

        result = strategy.to_polars(pandas_dataframe)

        # Default should be eager for most sources
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))


@pytest.mark.unit
class TestAsLazyParameterNarwhals:
    """Test the as_lazy parameter for to_narwhals() across all strategies."""

    @pytest.mark.parametrize("source_type,fixture_name", [
        ("pandas", "pandas_dataframe"),
        ("polars_eager", "polars_dataframe"),
        ("polars_lazy", "polars_lazyframe"),
    ])
    def test_to_narwhals_as_lazy_true_produces_lazyframe(self, request, source_type, fixture_name):
        """Test to_narwhals() with as_lazy=True produces Narwhals LazyFrame."""
        source_df = request.getfixturevalue(fixture_name)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(source_df)

        result = strategy.to_narwhals(source_df, as_lazy=True)

        assert isinstance(result, nw.LazyFrame), \
            f"{source_type} with as_lazy=True should produce Narwhals LazyFrame"

        # Verify data integrity
        collected = result.collect()
        assert len(collected) == 5

    @pytest.mark.parametrize("source_type,fixture_name", [
        ("pandas", "pandas_dataframe"),
        ("polars_eager", "polars_dataframe"),
        ("polars_lazy", "polars_lazyframe"),
    ])
    def test_to_narwhals_as_lazy_false_produces_dataframe(self, request, source_type, fixture_name):
        """Test to_narwhals() with as_lazy=False produces eager Narwhals DataFrame."""
        source_df = request.getfixturevalue(fixture_name)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(source_df)

        result = strategy.to_narwhals(source_df, as_lazy=False)

        assert isinstance(result, nw.DataFrame), \
            f"{source_type} with as_lazy=False should produce eager Narwhals DataFrame"

        # Verify data integrity
        assert len(result) == 5

    def test_to_narwhals_preserves_eager_by_default(self, pandas_dataframe):
        """Test to_narwhals() preserves eager type by default for pandas."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pandas_dataframe)

        result = strategy.to_narwhals(pandas_dataframe)

        # Pandas is eager, so should return eager Narwhals DataFrame
        assert isinstance(result, nw.DataFrame)
        assert not isinstance(result, nw.LazyFrame)

    def test_to_narwhals_preserves_lazy_by_default(self, polars_lazyframe):
        """Test to_narwhals() preserves lazy type by default for lazy sources."""
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(polars_lazyframe)

        result = strategy.to_narwhals(polars_lazyframe)

        # Polars LazyFrame is lazy, so should return Narwhals LazyFrame
        assert isinstance(result, nw.LazyFrame)

    def test_to_narwhals_pyarrow_default_eager(self, sample_data):
        """Test to_narwhals() returns eager for PyArrow by default."""
        pyarrow_table = pa.table(sample_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(pyarrow_table)

        result = strategy.to_narwhals(pyarrow_table)

        # PyArrow is eager, so should return eager Narwhals DataFrame
        assert isinstance(result, nw.DataFrame)
        assert not isinstance(result, nw.LazyFrame)

    def test_to_narwhals_ibis_handling(self, sample_data):
        """Test to_narwhals() with Ibis table (inherently lazy)."""
        ibis_table = DataFrameUtils.create_ibis(sample_data)
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(ibis_table)

        # Default should preserve Ibis lazy nature
        result_default = strategy.to_narwhals(ibis_table)
        assert isinstance(result_default, (nw.DataFrame, nw.LazyFrame))

        # Force lazy
        result_lazy = strategy.to_narwhals(ibis_table, as_lazy=True)
        assert isinstance(result_lazy, (nw.DataFrame, nw.LazyFrame))

        # Force eager
        result_eager = strategy.to_narwhals(ibis_table, as_lazy=False)
        assert isinstance(result_eager, nw.DataFrame)
        assert not isinstance(result_eager, nw.LazyFrame)

    def test_to_narwhals_roundtrip_with_as_lazy(self, pandas_dataframe):
        """Test roundtrip conversions with explicit as_lazy control."""
        factory = DataFrameCastFactory()

        # pandas -> narwhals lazy -> narwhals eager
        pandas_strategy = factory.get_strategy(pandas_dataframe)
        nw_lazy = pandas_strategy.to_narwhals(pandas_dataframe, as_lazy=True)
        assert isinstance(nw_lazy, nw.LazyFrame)

        nw_lazy_strategy = factory.get_strategy(nw_lazy)
        nw_eager = nw_lazy_strategy.to_narwhals(nw_lazy, as_lazy=False)
        assert isinstance(nw_eager, nw.DataFrame)
        assert not isinstance(nw_eager, nw.LazyFrame)

        # Verify data integrity
        assert len(nw_eager) == len(pandas_dataframe)


# ============================================================================
# PERFORMANCE AND OPTIMIZATION TESTS
# ============================================================================

@pytest.mark.unit
class TestLazyFrameOptimization:
    """Test that lazy evaluation optimizations work correctly."""

    def test_lazy_filter_not_materialized_until_needed(self, polars_lazyframe):
        """Test that lazy filter operations aren't materialized until needed."""
        # Apply multiple filters (should all remain lazy)
        filtered = (polars_lazyframe
                   .filter(pl.col("id") > 1)
                   .filter(pl.col("value") > 100.0)
                   .filter(pl.col("category") == "A"))

        # Should still be lazy
        assert isinstance(filtered, pl.LazyFrame)

        # Only materialize when converting
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(filtered)
        result = strategy.to_pandas(filtered)

        # Should have applied all filters
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert all(result['id'] > 1)
        assert all(result['value'] > 100.0)
        assert all(result['category'] == "A")

    def test_lazy_select_projection_optimization(self, polars_lazyframe):
        """Test that lazy select operations optimize projection."""
        # Select only specific columns (should remain lazy)
        selected = polars_lazyframe.select(["id", "name"])

        # Should still be lazy
        assert isinstance(selected, pl.LazyFrame)

        # Materialize
        factory = DataFrameCastFactory()
        strategy = factory.get_strategy(selected)
        result = strategy.to_pandas(selected)

        # Should only have selected columns
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["id", "name"]
