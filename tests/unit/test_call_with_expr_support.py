"""Unit tests for _call_with_expr_support error enrichment and _extract_literal_if_possible."""

import pytest
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK,
)
from mountainash.expressions.backends.expression_systems.polars.base import (
    PolarsBaseExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.ibis.base import (
    IbisBaseExpressionSystem,
)
from mountainash.expressions.backends.expression_systems.narwhals.base import (
    NarwhalsBaseExpressionSystem,
)


class TestCallWithExprSupport:

    def test_polars_success_passes_through(self):
        sys = PolarsBaseExpressionSystem()
        result = sys._call_with_expr_support(
            lambda: "ok",
            function_key=FK.CONTAINS,
            substring="hello",
        )
        assert result == "ok"

    def test_polars_unknown_error_propagates(self):
        sys = PolarsBaseExpressionSystem()

        def raise_runtime():
            raise RuntimeError("unrelated")

        with pytest.raises(RuntimeError, match="unrelated"):
            sys._call_with_expr_support(
                raise_runtime,
                function_key=FK.CONTAINS,
                substring="hello",
            )

    def test_narwhals_known_limitation_enriches_error(self):
        sys = NarwhalsBaseExpressionSystem()

        def raise_type_error():
            raise TypeError("expected a string")

        with pytest.raises(BackendCapabilityError, match="narwhals"):
            sys._call_with_expr_support(
                raise_type_error,
                function_key=FK.STARTS_WITH,
                substring="not_a_literal",
            )

    def test_ibis_no_limitations(self):
        sys = IbisBaseExpressionSystem()

        def raise_type_error():
            raise TypeError("some error")

        with pytest.raises(TypeError, match="some error"):
            sys._call_with_expr_support(
                raise_type_error,
                function_key=FK.STARTS_WITH,
                substring="hello",
            )


class TestExtractLiteralIfPossible:

    def test_polars_raw_value_passes_through(self):
        sys = PolarsBaseExpressionSystem()
        assert sys._extract_literal_if_possible("hello") == "hello"
        assert sys._extract_literal_if_possible(42) == 42
        assert sys._extract_literal_if_possible(None) is None

    def test_polars_literal_expr_extracts(self):
        import polars as pl

        sys = PolarsBaseExpressionSystem()
        result = sys._extract_literal_if_possible(pl.lit("hello"))
        assert result == "hello"

    def test_polars_column_ref_passes_through(self):
        import polars as pl

        sys = PolarsBaseExpressionSystem()
        col_expr = pl.col("name")
        result = sys._extract_literal_if_possible(col_expr)
        assert isinstance(result, pl.Expr)

    def test_narwhals_raw_value_passes_through(self):
        sys = NarwhalsBaseExpressionSystem()
        assert sys._extract_literal_if_possible("hello") == "hello"
        assert sys._extract_literal_if_possible(42) == 42

    def test_narwhals_literal_expr_extracts(self):
        import narwhals as nw

        sys = NarwhalsBaseExpressionSystem()
        result = sys._extract_literal_if_possible(nw.lit("hello"))
        assert result == "hello"

    def test_narwhals_column_ref_passes_through(self):
        import narwhals as nw

        sys = NarwhalsBaseExpressionSystem()
        col_expr = nw.col("name")
        result = sys._extract_literal_if_possible(col_expr)
        assert isinstance(result, nw.Expr)

    def test_ibis_always_passes_through(self):
        import ibis

        sys = IbisBaseExpressionSystem()
        lit_expr = ibis.literal("hello")
        result = sys._extract_literal_if_possible(lit_expr)
        assert result is lit_expr
