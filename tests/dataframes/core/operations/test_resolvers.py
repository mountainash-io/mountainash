"""
Tests for DataFrameResolver and SeriesResolver.

Tests the cross-backend resolution logic for expressions and series:
- DataFrameResolver: Resolves DataFrame wrapping for expression compatibility
- SeriesResolver: Resolves series conversion for DataFrame compatibility

Full matrix coverage:
- DataFrames: Polars, pandas, PyArrow, Ibis, Narwhals
- Expressions: pl.Expr, nw.Expr, ir.Expr, mountainash expressions
- Series: pl.Series, pd.Series, pa.Array, nw.Series
"""

import pytest
import polars as pl
import pandas as pd
import narwhals as nw
import pyarrow as pa
import ibis

from mountainash.dataframes.core.operations import (
    DataFrameResolver,
    SeriesResolver,
    ResolvedDataFrame,
    ResolvedSeries,
    is_expression,
    is_series,
)
from mountainash.dataframes.core.table_builder import table

# Try to import mountainash.expressions
try:
    from mountainash.expressions import col as ma_col
    HAS_MOUNTAINASH_EXPRESSIONS = True
except ImportError:
    HAS_MOUNTAINASH_EXPRESSIONS = False
    ma_col = None


# =============================================================================
# Type Detection Tests
# =============================================================================

class TestTypeDetection:
    """Test is_expression and is_series detection functions."""

    # Expression detection
    def test_polars_expression_detected(self):
        expr = pl.col("x") > 5
        assert is_expression(expr) is True
        assert is_series(expr) is False

    def test_narwhals_expression_detected(self):
        expr = nw.col("x") > 5
        assert is_expression(expr) is True
        assert is_series(expr) is False

    def test_ibis_expression_detected(self):
        t = ibis.memtable({"x": [1, 2, 3]})
        expr = t.x > 5
        assert is_expression(expr) is True
        assert is_series(expr) is False

    # Series detection
    def test_polars_series_detected(self):
        series = pl.Series([True, False, True])
        assert is_series(series) is True
        assert is_expression(series) is False

    def test_pandas_series_detected(self):
        series = pd.Series([True, False, True])
        assert is_series(series) is True
        assert is_expression(series) is False

    def test_pyarrow_array_detected(self):
        arr = pa.array([True, False, True])
        assert is_series(arr) is True
        assert is_expression(arr) is False

    def test_narwhals_series_detected(self):
        series = nw.from_native(pl.Series([True, False, True]), series_only=True)
        assert is_series(series) is True
        assert is_expression(series) is False


# =============================================================================
# DataFrameResolver Tests
# =============================================================================

class TestDataFrameResolver:
    """Test DataFrameResolver for expression compatibility."""

    def test_polars_expr_on_polars_df_no_wrap(self):
        """Native combination - no wrapping needed."""
        df = pl.DataFrame({"x": [1, 2, 3]})
        expr = pl.col("x") > 1

        resolved = DataFrameResolver.resolve(df, expr)

        assert resolved.wrap(df) is df  # Identity - no change
        assert resolved.unwrap(df) is df

    def test_narwhals_expr_on_polars_df_wraps(self):
        """nw.Expr on Polars - wraps in Narwhals."""
        df = pl.DataFrame({"x": [1, 2, 3]})
        expr = nw.col("x") > 1

        resolved = DataFrameResolver.resolve(df, expr)
        wrapped = resolved.wrap(df)

        # Should be wrapped in Narwhals
        assert "narwhals" in type(wrapped).__module__

        # Unwrap should return to native
        unwrapped = resolved.unwrap(wrapped)
        assert type(unwrapped).__module__.startswith("polars")

    def test_narwhals_expr_on_pandas_df_wraps(self):
        """nw.Expr on pandas - wraps in Narwhals."""
        df = pd.DataFrame({"x": [1, 2, 3]})
        expr = nw.col("x") > 1

        resolved = DataFrameResolver.resolve(df, expr)
        wrapped = resolved.wrap(df)

        # Should be wrapped in Narwhals
        assert "narwhals" in type(wrapped).__module__

        # Unwrap should return to native pandas
        unwrapped = resolved.unwrap(wrapped)
        assert type(unwrapped).__module__.startswith("pandas")

    def test_narwhals_expr_on_pyarrow_df_wraps(self):
        """nw.Expr on PyArrow - wraps in Narwhals."""
        df = pa.table({"x": [1, 2, 3]})
        expr = nw.col("x") > 1

        resolved = DataFrameResolver.resolve(df, expr)
        wrapped = resolved.wrap(df)

        # Should be wrapped in Narwhals
        assert "narwhals" in type(wrapped).__module__


# =============================================================================
# SeriesResolver Tests
# =============================================================================

class TestSeriesResolver:
    """Test SeriesResolver for series conversion."""

    def test_polars_series_on_polars_df_no_conversion(self):
        """Same backend - no conversion needed."""
        df = pl.DataFrame({"x": [1, 2, 3]})
        series = pl.Series([True, False, True])

        resolved = SeriesResolver.resolve(df, series)

        assert resolved.series is series  # No conversion
        assert resolved.prepare_df(df) is df  # No change

    def test_pandas_series_on_pandas_df_no_conversion(self):
        """Same backend - no conversion needed."""
        df = pd.DataFrame({"x": [1, 2, 3]})
        series = pd.Series([True, False, True])

        resolved = SeriesResolver.resolve(df, series)

        assert resolved.series is series
        assert resolved.prepare_df(df) is df

    def test_pandas_series_on_polars_df_converts(self):
        """Cross-backend - converts series to match DataFrame."""
        df = pl.DataFrame({"x": [1, 2, 3]})
        series = pd.Series([True, False, True])

        resolved = SeriesResolver.resolve(df, series)

        # Series should be converted to Polars
        assert type(resolved.series).__module__.startswith("polars")
        assert resolved.prepare_df(df) is df

    def test_polars_series_on_pandas_df_converts(self):
        """Cross-backend - converts series to match DataFrame."""
        df = pd.DataFrame({"x": [1, 2, 3]})
        series = pl.Series([True, False, True])

        resolved = SeriesResolver.resolve(df, series)

        # Series should be converted to pandas
        assert type(resolved.series).__module__.startswith("pandas")

    def test_narwhals_series_unwrapped(self):
        """nw.Series is unwrapped before resolution."""
        df = pl.DataFrame({"x": [1, 2, 3]})
        nw_series = nw.from_native(pl.Series([True, False, True]), series_only=True)

        resolved = SeriesResolver.resolve(df, nw_series)

        # Should be unwrapped to native Polars
        assert type(resolved.series).__module__.startswith("polars")


# =============================================================================
# Integration Tests - Filter with TableBuilder
# =============================================================================

class TestFilterIntegration:
    """Integration tests using table().filter() with various backends."""

    # DataFrame backends to test
    @pytest.fixture(params=["polars", "pandas"])
    def df_backend(self, request):
        return request.param

    @pytest.fixture
    def sample_df(self, df_backend):
        data = {"x": [1, 2, 3, 4, 5], "y": ["a", "b", "c", "d", "e"]}
        if df_backend == "polars":
            return pl.DataFrame(data)
        else:
            return pd.DataFrame(data)

    # Expression filter tests

    def test_filter_polars_expr_on_polars(self):
        """pl.Expr on Polars DataFrame."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(pl.col("x") > 2).df
        assert len(result) == 3

    def test_filter_narwhals_expr_on_polars(self):
        """nw.Expr on Polars DataFrame."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(nw.col("x") > 3).df
        assert len(result) == 2

    def test_filter_narwhals_expr_on_pandas(self):
        """nw.Expr on pandas DataFrame."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(nw.col("x") > 2).df
        assert len(result) == 3

    # Series filter tests (boolean mask)

    def test_filter_polars_series_on_polars(self):
        """pl.Series mask on Polars DataFrame."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pl.Series([True, False, True, False, True])
        result = table(df).filter(mask).df
        assert len(result) == 3

    def test_filter_pandas_series_on_pandas(self):
        """pd.Series mask on pandas DataFrame."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pd.Series([True, False, True, False, True])
        result = table(df).filter(mask).df
        assert len(result) == 3

    # Cross-backend series tests

    def test_filter_pandas_series_on_polars(self):
        """pd.Series mask on Polars DataFrame (cross-backend)."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pd.Series([False, False, True, True, True])
        result = table(df).filter(mask).df
        assert len(result) == 3

    def test_filter_polars_series_on_pandas(self):
        """pl.Series mask on pandas DataFrame (cross-backend)."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pl.Series([True, True, False, False, False])
        result = table(df).filter(mask).df
        assert len(result) == 2


# =============================================================================
# Matrix Test - All Combinations
# =============================================================================

class TestDataFrameExpressionMatrix:
    """
    Full matrix: DataFrame backends × Expression types.

    DataFrame backends: Polars, pandas, PyArrow
    Expression types: pl.Expr, nw.Expr

    Valid combinations:
    - pl.Expr: Only works on Polars DataFrames
    - nw.Expr: Works on all backends (wraps DataFrame in Narwhals)
    """

    # All DataFrame types
    @pytest.fixture(params=["polars", "pandas", "pyarrow"])
    def df_with_type(self, request):
        data = {"x": [1, 2, 3, 4, 5], "y": ["a", "b", "c", "d", "e"]}
        if request.param == "polars":
            return pl.DataFrame(data), "polars"
        elif request.param == "pandas":
            return pd.DataFrame(data), "pandas"
        else:
            return pa.table(data), "pyarrow"

    def test_polars_expr_on_polars(self):
        """pl.Expr on Polars - native, no wrapping."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(pl.col("x") > 2).df
        assert len(result) == 3

    def test_narwhals_expr_on_polars(self):
        """nw.Expr on Polars - wraps in Narwhals."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(nw.col("x") > 2).df
        assert len(result) == 3
        assert isinstance(result, pl.DataFrame)

    def test_narwhals_expr_on_pandas(self):
        """nw.Expr on pandas - wraps in Narwhals, unwraps to pandas."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(nw.col("x") > 2).df
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)

    def test_narwhals_expr_on_pyarrow(self):
        """nw.Expr on PyArrow - wraps in Narwhals, unwraps to PyArrow."""
        df = pa.table({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(nw.col("x") > 2).df
        assert len(result) == 3
        assert isinstance(result, pa.Table)


class TestDataFrameSeriesMatrix:
    """
    Full matrix: DataFrame backends × Series types.

    DataFrame backends: Polars, pandas, PyArrow
    Series types: pl.Series, pd.Series, pa.Array, nw.Series

    All combinations should work via SeriesResolver conversion.
    """

    MASK_TRUE_FALSE_TRUE_FALSE_TRUE = [True, False, True, False, True]

    # -------------------------------------------------------------------------
    # Polars DataFrame with all series types
    # -------------------------------------------------------------------------

    def test_polars_series_on_polars_df(self):
        """pl.Series on Polars - native, no conversion."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pl.Series(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pl.DataFrame)

    def test_pandas_series_on_polars_df(self):
        """pd.Series on Polars - converts to pl.Series."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pd.Series(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pl.DataFrame)

    def test_pyarrow_array_on_polars_df(self):
        """pa.Array on Polars - converts to pl.Series."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pa.array(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pl.DataFrame)

    def test_narwhals_series_on_polars_df(self):
        """nw.Series on Polars - unwraps to native, no conversion needed."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = nw.from_native(pl.Series(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE), series_only=True)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pl.DataFrame)

    # -------------------------------------------------------------------------
    # pandas DataFrame with all series types
    # -------------------------------------------------------------------------

    def test_pandas_series_on_pandas_df(self):
        """pd.Series on pandas - native, no conversion."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pd.Series(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)

    def test_polars_series_on_pandas_df(self):
        """pl.Series on pandas - converts to pd.Series."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pl.Series(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)

    def test_pyarrow_array_on_pandas_df(self):
        """pa.Array on pandas - converts to pd.Series."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        mask = pa.array(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)

    def test_narwhals_series_on_pandas_df(self):
        """nw.Series on pandas - unwraps to native, converts if needed."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        # nw.Series wrapping a pandas series
        mask = nw.from_native(pd.Series(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE), series_only=True)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)

    # -------------------------------------------------------------------------
    # PyArrow Table with all series types
    # -------------------------------------------------------------------------

    def test_pyarrow_array_on_pyarrow_table(self):
        """pa.Array on PyArrow - native, no conversion."""
        df = pa.table({"x": [1, 2, 3, 4, 5]})
        mask = pa.array(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pa.Table)

    def test_polars_series_on_pyarrow_table(self):
        """pl.Series on PyArrow - converts to pa.Array."""
        df = pa.table({"x": [1, 2, 3, 4, 5]})
        mask = pl.Series(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pa.Table)

    def test_pandas_series_on_pyarrow_table(self):
        """pd.Series on PyArrow - converts to pa.Array."""
        df = pa.table({"x": [1, 2, 3, 4, 5]})
        mask = pd.Series(self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pa.Table)

    def test_narwhals_series_on_pyarrow_table(self):
        """nw.Series on PyArrow - unwraps to native, converts if needed."""
        df = pa.table({"x": [1, 2, 3, 4, 5]})
        mask = nw.from_native(pa.chunked_array([self.MASK_TRUE_FALSE_TRUE_FALSE_TRUE]), series_only=True)
        result = table(df).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pa.Table)


class TestParameterizedMatrix:
    """
    Parameterized version of the full matrix for compact test output.
    """

    @pytest.mark.parametrize(
        "df_type,expr_type,expected_len",
        [
            ("polars", "polars", 3),
            ("polars", "narwhals", 3),
            ("pandas", "narwhals", 3),
            ("pyarrow", "narwhals", 3),
        ],
    )
    def test_expression_filter_matrix(self, df_type, expr_type, expected_len):
        """Parameterized: DataFrame × Expression."""
        data = {"x": [1, 2, 3, 4, 5]}
        if df_type == "polars":
            df = pl.DataFrame(data)
        elif df_type == "pandas":
            df = pd.DataFrame(data)
        else:
            df = pa.table(data)

        if expr_type == "polars":
            expr = pl.col("x") > 2
        else:
            expr = nw.col("x") > 2

        result = table(df).filter(expr).df
        assert len(result) == expected_len

    @pytest.mark.parametrize(
        "df_type,series_type",
        [
            # Polars DataFrame
            ("polars", "polars"),
            ("polars", "pandas"),
            ("polars", "pyarrow"),
            # pandas DataFrame
            ("pandas", "polars"),
            ("pandas", "pandas"),
            ("pandas", "pyarrow"),
            # PyArrow Table
            ("pyarrow", "polars"),
            ("pyarrow", "pandas"),
            ("pyarrow", "pyarrow"),
        ],
    )
    def test_series_filter_matrix(self, df_type, series_type):
        """Parameterized: DataFrame × Series (3×3 = 9 combinations)."""
        data = {"x": [1, 2, 3, 4, 5]}
        mask_data = [True, False, True, False, True]

        # Create DataFrame
        if df_type == "polars":
            df = pl.DataFrame(data)
        elif df_type == "pandas":
            df = pd.DataFrame(data)
        else:
            df = pa.table(data)

        # Create Series
        if series_type == "polars":
            mask = pl.Series(mask_data)
        elif series_type == "pandas":
            mask = pd.Series(mask_data)
        else:
            mask = pa.array(mask_data)

        result = table(df).filter(mask).df
        assert len(result) == 3


# =============================================================================
# Ibis DataFrame Tests
# =============================================================================

class TestIbisDataFrame:
    """
    Tests for Ibis tables with expressions and series.

    Ibis is lazy - operations build up a query that executes on materialization.
    Series filters require materializing the Ibis table first.
    """

    @pytest.fixture
    def ibis_table(self):
        return ibis.memtable({"x": [1, 2, 3, 4, 5], "y": ["a", "b", "c", "d", "e"]})

    # Ibis expressions on Ibis tables (native)
    def test_ibis_expr_on_ibis_table(self, ibis_table):
        """ir.Expr on Ibis - native, no wrapping."""
        expr = ibis_table.x > 2
        result = table(ibis_table).filter(expr).df
        # Ibis returns an Ibis table, need to materialize to check length
        assert result.count().execute() == 3

    # Narwhals expressions on Ibis tables (materialize + wrap)
    def test_narwhals_expr_on_ibis_table(self, ibis_table):
        """nw.Expr on Ibis - materializes to PyArrow, wraps in Narwhals."""
        result = table(ibis_table).filter(nw.col("x") > 2).df
        # Result should be PyArrow after unwrapping from Narwhals
        assert len(result) == 3

    # Series on Ibis tables (materialize to match series backend)
    def test_polars_series_on_ibis_table(self, ibis_table):
        """pl.Series on Ibis - materializes Ibis to Polars."""
        mask = pl.Series([True, False, True, False, True])
        result = table(ibis_table).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pl.DataFrame)

    def test_pandas_series_on_ibis_table(self, ibis_table):
        """pd.Series on Ibis - materializes Ibis to pandas."""
        mask = pd.Series([True, False, True, False, True])
        result = table(ibis_table).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)

    def test_pyarrow_array_on_ibis_table(self, ibis_table):
        """pa.Array on Ibis - materializes Ibis to PyArrow."""
        mask = pa.array([True, False, True, False, True])
        result = table(ibis_table).filter(mask).df
        assert len(result) == 3
        assert isinstance(result, pa.Table)


# =============================================================================
# Narwhals DataFrame Tests
# =============================================================================

class TestNarwhalsDataFrame:
    """
    Tests for Narwhals-wrapped DataFrames with expressions and series.

    Narwhals DataFrames are wrappers around native DataFrames.
    They should work with nw.Expr natively.
    """

    @pytest.fixture(params=["polars", "pandas", "pyarrow"])
    def narwhals_df(self, request):
        data = {"x": [1, 2, 3, 4, 5], "y": ["a", "b", "c", "d", "e"]}
        if request.param == "polars":
            native = pl.DataFrame(data)
        elif request.param == "pandas":
            native = pd.DataFrame(data)
        else:
            native = pa.table(data)
        return nw.from_native(native, eager_only=True), request.param

    def test_narwhals_expr_on_narwhals_df(self, narwhals_df):
        """nw.Expr on Narwhals DataFrame - native, no wrapping needed."""
        df, backend = narwhals_df
        result = table(df).filter(nw.col("x") > 2).df
        assert len(result) == 3

    def test_polars_series_on_narwhals_df(self, narwhals_df):
        """pl.Series on Narwhals DataFrame."""
        df, backend = narwhals_df
        mask = pl.Series([True, False, True, False, True])
        result = table(df).filter(mask).df
        assert len(result) == 3

    def test_pandas_series_on_narwhals_df(self, narwhals_df):
        """pd.Series on Narwhals DataFrame."""
        df, backend = narwhals_df
        mask = pd.Series([True, False, True, False, True])
        result = table(df).filter(mask).df
        assert len(result) == 3


# =============================================================================
# Mountainash Expression Tests
# =============================================================================

@pytest.mark.skipif(not HAS_MOUNTAINASH_EXPRESSIONS, reason="mountainash.expressions not installed")
class TestMountainashExpressions:
    """
    Tests for mountainash expressions on all DataFrame backends.

    Mountainash expressions are backend-agnostic and get compiled
    to native expressions based on the DataFrame backend.
    """

    def test_mountainash_expr_on_polars(self):
        """mountainash expression on Polars DataFrame."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(ma_col("x").gt(2)).df
        assert len(result) == 3
        assert isinstance(result, pl.DataFrame)

    def test_mountainash_expr_on_pandas(self):
        """mountainash expression on pandas DataFrame."""
        df = pd.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(ma_col("x").gt(2)).df
        assert len(result) == 3
        assert isinstance(result, pd.DataFrame)

    def test_mountainash_expr_on_pyarrow(self):
        """mountainash expression on PyArrow Table."""
        df = pa.table({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(ma_col("x").gt(2)).df
        assert len(result) == 3
        assert isinstance(result, pa.Table)

    def test_mountainash_expr_on_ibis(self):
        """mountainash expression on Ibis Table."""
        df = ibis.memtable({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(ma_col("x").gt(2)).df
        assert result.count().execute() == 3

    def test_mountainash_expr_on_narwhals(self):
        """mountainash expression on Narwhals DataFrame."""
        native = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        df = nw.from_native(native, eager_only=True)
        result = table(df).filter(ma_col("x").gt(2)).df
        assert len(result) == 3

    def test_mountainash_complex_expr(self):
        """mountainash complex expression (AND, OR)."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})
        # x > 2 AND y < 50
        result = table(df).filter(ma_col("x").gt(2).and_(ma_col("y").lt(50))).df
        assert len(result) == 2  # rows 3 and 4 (x=3,y=30 and x=4,y=40)


# =============================================================================
# Full Backend Matrix - Parameterized
# =============================================================================

class TestFullBackendMatrix:
    """
    Comprehensive parameterized tests covering all backend combinations.

    DataFrame backends: polars, pandas, pyarrow, ibis, narwhals
    Expression types: polars, narwhals, ibis
    Series types: polars, pandas, pyarrow, narwhals
    """

    @pytest.fixture
    def create_dataframe(self):
        """Factory to create DataFrames of different backends."""
        def _create(backend: str, data: dict):
            if backend == "polars":
                return pl.DataFrame(data)
            elif backend == "pandas":
                return pd.DataFrame(data)
            elif backend == "pyarrow":
                return pa.table(data)
            elif backend == "ibis":
                return ibis.memtable(data)
            elif backend == "narwhals":
                return nw.from_native(pl.DataFrame(data), eager_only=True)
            else:
                raise ValueError(f"Unknown backend: {backend}")
        return _create

    @pytest.fixture
    def create_series(self):
        """Factory to create series of different backends."""
        def _create(backend: str, data: list):
            if backend == "polars":
                return pl.Series(data)
            elif backend == "pandas":
                return pd.Series(data)
            elif backend == "pyarrow":
                return pa.array(data)
            elif backend == "narwhals":
                return nw.from_native(pl.Series(data), series_only=True)
            else:
                raise ValueError(f"Unknown backend: {backend}")
        return _create

    # Expression matrix: DataFrame × Expression type
    @pytest.mark.parametrize(
        "df_backend,expr_type",
        [
            # Polars DataFrame
            ("polars", "polars"),
            ("polars", "narwhals"),
            # pandas DataFrame
            ("pandas", "narwhals"),
            # PyArrow Table
            ("pyarrow", "narwhals"),
            # Ibis Table
            ("ibis", "ibis"),
            ("ibis", "narwhals"),
            # Narwhals DataFrame
            ("narwhals", "narwhals"),
        ],
    )
    def test_expression_backend_matrix(self, df_backend, expr_type, create_dataframe):
        """Test all valid DataFrame × Expression combinations."""
        data = {"x": [1, 2, 3, 4, 5]}
        df = create_dataframe(df_backend, data)

        if expr_type == "polars":
            expr = pl.col("x") > 2
        elif expr_type == "narwhals":
            expr = nw.col("x") > 2
        elif expr_type == "ibis":
            # Ibis expressions need the table reference
            expr = df.x > 2

        result = table(df).filter(expr).df

        # Check result length (Ibis needs .execute())
        if df_backend == "ibis" and expr_type == "ibis":
            assert result.count().execute() == 3
        else:
            assert len(result) == 3

    # Series matrix: DataFrame × Series type
    @pytest.mark.parametrize(
        "df_backend,series_backend",
        [
            # Polars DataFrame with all series types
            ("polars", "polars"),
            ("polars", "pandas"),
            ("polars", "pyarrow"),
            ("polars", "narwhals"),
            # pandas DataFrame with all series types
            ("pandas", "polars"),
            ("pandas", "pandas"),
            ("pandas", "pyarrow"),
            ("pandas", "narwhals"),
            # PyArrow Table with all series types
            ("pyarrow", "polars"),
            ("pyarrow", "pandas"),
            ("pyarrow", "pyarrow"),
            ("pyarrow", "narwhals"),
            # Ibis Table with all series types (materializes)
            ("ibis", "polars"),
            ("ibis", "pandas"),
            ("ibis", "pyarrow"),
            # Narwhals DataFrame with all series types
            ("narwhals", "polars"),
            ("narwhals", "pandas"),
            ("narwhals", "pyarrow"),
            ("narwhals", "narwhals"),
        ],
    )
    def test_series_backend_matrix(self, df_backend, series_backend, create_dataframe, create_series):
        """Test all DataFrame × Series combinations (5×4 = 20 combinations)."""
        data = {"x": [1, 2, 3, 4, 5]}
        mask_data = [True, False, True, False, True]

        df = create_dataframe(df_backend, data)
        mask = create_series(series_backend, mask_data)

        result = table(df).filter(mask).df
        assert len(result) == 3
