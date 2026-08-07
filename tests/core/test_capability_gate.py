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
        df = pl.DataFrame({"v": [1, 2], "other": [1, 3]})
        lit_path = ma.t_col("v").t_is_in([1, 5]).compile(df)
        assert lit_path is not None
        # Expression MEMBERS (OR-chain path) still work. A *bare* column
        # collection now raises BareExpressionCollectionError — use
        # .list.t_contains for per-row list membership.
        expr_path = ma.t_col("v").t_is_in([ma.col("other")]).compile(df)
        assert expr_path is not None


from mountainash.core.capabilities import (
    Boundary,
    WILDCARD_PARAM,
    Enforcement,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)
from mountainash.expressions.core.expression_system.expsys_base import get_expression_system
from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor


def _compile_polars(expr):
    system = get_expression_system(CONST_BACKEND.POLARS)(dialect="polars")
    return UnifiedExpressionVisitor(system, enforce_capabilities=True).visit(expr._node)


@pytest.fixture
def isolated_registry():
    snap = CapabilityRegistry.snapshot()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snap)


def test_op_level_gate_raises_for_zero_arg_op(isolated_registry):
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [
        CapabilityFact(
            operation_key=FK_DT.TODAY, param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.POLARS,
            dialect=None, message="today unsupported (test)", since="2026-07-29",
        )
    ])
    with pytest.raises(BackendCapabilityError):
        _compile_polars(ma.today())


def test_op_level_gate_ignores_dialect_scoped_expr_capable(isolated_registry):
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [
        CapabilityFact(
            operation_key=FK_DT.TODAY, param=WILDCARD_PARAM,
            level=CapabilityLevel.EXPR_CAPABLE, backend=CONST_BACKEND.POLARS,
            dialect="polars", message="refinement (test)", since="2026-07-29",
            probe_exempt="refinement",
        )
    ])
    _compile_polars(ma.today())  # no raise


def test_op_level_gate_ignores_router_metadata(isolated_registry):
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [
        CapabilityFact(
            operation_key=FK_DT.TODAY, param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.POLARS,
            dialect=None, message="router only (test)", since="2026-07-29",
            enforcement=Enforcement.ROUTER_METADATA,  # boundary defaults to BUILD (legal)
        )
    ])
    _compile_polars(ma.today())  # no raise


def test_op_level_gate_ignores_materialize_residue(isolated_registry):
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [
        CapabilityFact(
            operation_key=FK_DT.TODAY, param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.POLARS,
            dialect=None, message="residue only (test)", since="2026-07-29",
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            boundary=Boundary.MATERIALIZE, native_errors=(ValueError,),  # required for MATERIALIZE
        )
    ])
    _compile_polars(ma.today())  # no raise


def test_op_level_gate_no_fact_compiles():
    _compile_polars(ma.today())  # no raise


def test_enforced_visitor_construction_bootstraps_declarations():
    """Cold-path regression guard: a gating consumer must load the capability
    declaration modules before it can gate. Constructing an enforce_capabilities
    visitor triggers load_all_capability_declarations(), so gates fire even on a
    cold path where nothing else imported the declaration module. Runs in a fresh
    interpreter because the registry's _load_state is already LOADED in-process.
    Asserts CapabilityRegistry._load_state is _LoadState.UNINITIALIZED / LOADED
    (spec §2 state machine) — not a derived boolean — so a regression where
    _load_state gains a fifth state (e.g. PARTIAL) cannot silently collapse to
    a True/False check."""
    import subprocess
    import sys

    code = (
        "import mountainash.core.capabilities.bootstrap as b\n"
        "from mountainash.expressions.core.unified_visitor import UnifiedExpressionVisitor\n"
        "from mountainash.core.capabilities.registry import (\n"
        "    CapabilityRegistry, _LoadState,\n"
        ")\n"
        "assert CapabilityRegistry._load_state is _LoadState.UNINITIALIZED, (\n"
        "    'importing the visitor must not bootstrap by itself'\n"
        ")\n"
        "UnifiedExpressionVisitor(object(), enforce_capabilities=False)\n"
        "assert CapabilityRegistry._load_state is _LoadState.UNINITIALIZED, (\n"
        "    'a non-enforcing visitor must not bootstrap'\n"
        ")\n"
        "UnifiedExpressionVisitor(object(), enforce_capabilities=True)\n"
        "assert CapabilityRegistry._load_state is _LoadState.LOADED, (\n"
        "    'enforced visitor construction did not bootstrap declarations'\n"
        ")\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)

