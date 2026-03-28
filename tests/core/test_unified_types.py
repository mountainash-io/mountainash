"""Tests for unified type aliases in mountainash.core.types."""

import pytest

from mountainash.core.types import (
    # DataFrame types
    PandasFrame,
    PolarsFrame,
    PolarsLazyFrame,
    PyArrowTable,
    IbisTable,
    NarwhalsFrame,
    NarwhalsLazyFrame,
    # Expression types
    PolarsExpr,
    IbisExpr,
    NarwhalsExpr,
    # Series types
    PandasSeries,
    PolarsSeries,
    NarwhalsSeries,
    PyArrowArray,
    # Unions
    SupportedDataFrames,
    SupportedExpressions,
    SupportedSeries,
    # Protocols
    DataFrameLike,
    LazyFrameLike,
    ExpressionLike,
    # Type guards
    is_polars_dataframe,
    is_pandas_dataframe,
    is_polars_expression,
    detect_dataframe_backend_type,
)


class TestCoreTypesImportable:
    """All shared types are importable from core."""

    def test_dataframe_types(self):
        assert PandasFrame is not None
        assert PolarsFrame is not None
        assert PolarsLazyFrame is not None
        assert PyArrowTable is not None
        assert IbisTable is not None
        assert NarwhalsFrame is not None
        assert NarwhalsLazyFrame is not None

    def test_expression_types(self):
        assert PolarsExpr is not None
        assert IbisExpr is not None
        assert NarwhalsExpr is not None

    def test_series_types(self):
        assert PandasSeries is not None
        assert PolarsSeries is not None
        assert NarwhalsSeries is not None
        assert PyArrowArray is not None

    def test_protocols(self):
        assert DataFrameLike is not None
        assert LazyFrameLike is not None
        assert ExpressionLike is not None

    def test_type_guards(self):
        assert callable(is_polars_dataframe)
        assert callable(is_pandas_dataframe)
        assert callable(is_polars_expression)
        assert callable(detect_dataframe_backend_type)


class TestShimIdentity:
    """Types from old import paths are identical to core types."""

    def test_dataframes_typing_polars_expr(self):
        from mountainash.dataframes.core.typing import PolarsExpr as df_PolarsExpr
        assert df_PolarsExpr is PolarsExpr

    def test_dataframes_typing_supported_dataframes(self):
        from mountainash.dataframes.core.typing import SupportedDataFrames as df_SD
        assert df_SD is SupportedDataFrames

    def test_dataframes_typing_supported_expressions(self):
        from mountainash.dataframes.core.typing import SupportedExpressions as df_SE
        assert df_SE is SupportedExpressions

    def test_dataframes_typing_polars_frame(self):
        from mountainash.dataframes.core.typing import PolarsFrame as df_PF
        assert df_PF is PolarsFrame

    def test_dataframes_typing_pandas_series(self):
        from mountainash.dataframes.core.typing import PandasSeries as df_PS
        assert df_PS is PandasSeries

    def test_expressions_types_polars_expr(self):
        from mountainash.expressions.types import PolarsExpr as expr_PolarsExpr
        assert expr_PolarsExpr is PolarsExpr

    def test_expressions_types_supported_expressions(self):
        from mountainash.expressions.types import SupportedExpressions as expr_SE
        assert expr_SE is SupportedExpressions


class TestTypeGuardsWithRealObjects:
    """Type guards work with actual backend objects."""

    def test_polars_dataframe_detection(self):
        import polars as pl
        df = pl.DataFrame({"a": [1, 2, 3]})
        assert is_polars_dataframe(df)
        assert not is_pandas_dataframe(df)

    def test_polars_expression_detection(self):
        import polars as pl
        expr = pl.col("a")
        assert is_polars_expression(expr)

    def test_detect_polars_backend(self):
        import polars as pl
        df = pl.DataFrame({"a": [1]})
        assert detect_dataframe_backend_type(df) == "polars"
