"""Tests for unified type aliases in mountainash.core.types."""

from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

from mountainash.core.types import (
    # TypeVars (runtime-available)
    DataFrameT,
    ExpressionT,
    SeriesT,
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

if TYPE_CHECKING:
    from mountainash.core.types import (
        PandasFrame,
        PolarsFrame,
        PolarsLazyFrame,
        PyArrowTable,
        IbisTable,
        NarwhalsFrame,
        NarwhalsLazyFrame,
        PolarsExpr,
        IbisExpr,
        NarwhalsExpr,
        PandasSeries,
        PolarsSeries,
        NarwhalsSeries,
        PyArrowArray,
        SupportedDataFrames,
        SupportedExpressions,
        SupportedSeries,
    )


class TestCoreTypesImportable:
    """Runtime-available types are importable from core."""

    def test_typevars(self):
        assert DataFrameT is not None
        assert ExpressionT is not None
        assert SeriesT is not None

    def test_protocols(self):
        assert DataFrameLike is not None
        assert LazyFrameLike is not None
        assert ExpressionLike is not None

    def test_type_guards(self):
        assert callable(is_polars_dataframe)
        assert callable(is_pandas_dataframe)
        assert callable(is_polars_expression)
        assert callable(detect_dataframe_backend_type)

    def test_type_aliases_are_type_checking_only(self):
        """Type aliases are only available under TYPE_CHECKING, not at runtime."""
        import mountainash.core.types as types_mod
        # These should NOT be in the module namespace at runtime
        assert not hasattr(types_mod, 'PandasFrame')
        assert not hasattr(types_mod, 'PolarsFrame')
        assert not hasattr(types_mod, 'SupportedDataFrames')


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
