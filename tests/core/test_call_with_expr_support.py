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

    def test_narwhals_build_fact_does_not_enrich(self):
        sys = NarwhalsBaseExpressionSystem()

        def raise_type_error():
            raise TypeError("expected a string")

        # BUILD facts gate at the visitor, not here.
        with pytest.raises(TypeError):
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
    """Only Ibis retains ``_extract_literal_if_possible`` (its replace()
    extraction-without-narrowing override). The base default and the
    polars/narwhals overrides were retired in the spine's Phase 1 —
    extraction moved to the visitor gate; their absence is guarded by
    ``test_capability_integrity.test_no_extractor_heuristics_remain``."""

    def test_ibis_extracts_literal(self):
        import ibis

        sys = IbisBaseExpressionSystem()
        lit_expr = ibis.literal("hello")
        result = sys._extract_literal_if_possible(lit_expr)
        assert result == "hello"

    def test_ibis_column_ref_passes_through(self):
        import ibis

        sys = IbisBaseExpressionSystem()
        # Column references (non-literal Scalars) should pass through
        raw_val = 42
        result = sys._extract_literal_if_possible(raw_val)
        assert result == 42
