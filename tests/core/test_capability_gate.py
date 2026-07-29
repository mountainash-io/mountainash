"""Compile-time capability gate at the expression visitor (spec Section 2)."""
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


@pytest.fixture(autouse=True)
def _isolated_registry():
    snapshot = CapabilityRegistry.snapshot()
    yield
    CapabilityRegistry.restore(snapshot)


def _register(level, param="substring", condition=None, **kw):
    CapabilityRegistry.register_backend(
        CONST_BACKEND.POLARS,
        [CapabilityFact(
            operation_key=FK_STR.CONTAINS, param=param, level=level,
            backend=CONST_BACKEND.POLARS,
            message="test-fact: contains substring gated",
            workaround="use a literal",
            since="2026-07-05", condition=condition, **kw,
        )],
    )


DF = pl.DataFrame({"text": ["abc"], "pat": ["b"]})


class TestLiteralOnlyGate:
    def test_dynamic_arg_raises_at_compile_with_metadata(self):
        _register(CapabilityLevel.LITERAL_ONLY)
        with pytest.raises(BackendCapabilityError) as exc_info:
            ma.col("text").str.contains(ma.col("pat")).compile(DF)
        assert "test-fact" in str(exc_info.value)
        assert "Workaround: use a literal" in str(exc_info.value)

    def test_literal_arg_passes_raw_value(self):
        _register(CapabilityLevel.LITERAL_ONLY)
        compiled = ma.col("text").str.contains("b").compile(DF)
        assert DF.select(compiled).to_series().to_list() == [True]

    def test_lit_node_unwrapped_to_raw(self):
        _register(CapabilityLevel.LITERAL_ONLY)
        compiled = ma.col("text").str.contains(ma.lit("b")).compile(DF)
        assert DF.select(compiled).to_series().to_list() == [True]


class TestUnsupportedGate:
    def test_raises_before_backend_call(self):
        _register(CapabilityLevel.UNSUPPORTED)
        with pytest.raises(BackendCapabilityError):
            ma.col("text").str.contains("b").compile(DF)


class TestConditionIsProseOnly:
    """Backlog 66a: a prose condition no longer disables gating.

    This class previously asserted the inverse (TestConditionedFactsDoNotGate).
    The spec makes that behaviour the defect: adding documentation to a fact
    silently turned its capability off, with every test still passing.
    """

    def test_conditioned_fact_with_default_enforcement_gates(self):
        _register(CapabilityLevel.LITERAL_ONLY, condition="only when x")
        with pytest.raises(BackendCapabilityError):
            ma.col("text").str.contains(ma.col("pat")).compile(DF)

    def test_non_gate_enforcement_skips_the_structural_gate(self):
        from mountainash.core.capabilities import Boundary, Enforcement

        _register(
            CapabilityLevel.LITERAL_ONLY,
            condition="collection compiles to an expression",
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            boundary=Boundary.MATERIALIZE,
            native_errors=(ValueError,),
        )
        compiled = ma.col("text").str.contains(ma.col("pat")).compile(DF)
        assert compiled is not None


class TestGateBypass:
    def test_enforce_capabilities_false_skips_gate(self):
        _register(CapabilityLevel.LITERAL_ONLY)
        from mountainash.expressions.backends.expression_systems.polars import (
            PolarsExpressionSystem,  # composed system, exported by polars/__init__.py
        )
        from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor

        visitor = UnifiedExpressionVisitor(
            PolarsExpressionSystem(), enforce_capabilities=False
        )
        node = ma.col("text").str.contains(ma.col("pat"))._node
        assert visitor.visit(node) is not None  # native polars accepts Expr here


class TestPolymorphicPreserved:
    def test_is_in_literal_list_and_expression_paths_still_work(self):
        # Regression: _raw_value_functions semantics now come from core facts.
        df = pl.DataFrame({"v": [1, 2], "allowed": [[1], [3]]})
        lit_path = ma.t_col("v").t_is_in([1, 5]).compile(df)
        assert lit_path is not None
        expr_path = ma.t_col("v").t_is_in(ma.col("allowed")).compile(df)
        assert expr_path is not None
