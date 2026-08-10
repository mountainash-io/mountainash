"""Focused contracts for the argument-matrix's spine-derived xfail expectations.

These tests pin the mechanism `_test_template.py` uses to derive strict xfail
markers from the exact bound AST each matrix cell compiles — see backlog
arg-matrix-xfail-blind-to-value-class-facts and spec
2026-08-09-argument-matrix-value-class-facts-design.
"""
from __future__ import annotations

import pytest

from mountainash.core.constants import CONST_BACKEND

from expressions.argument_types.conftest import ALL_BACKENDS, make_df, matrix_identity


@pytest.mark.parametrize("backend", ALL_BACKENDS)
def test_matrix_identity_matches_production_backend_detection(backend: str) -> None:
    from tests.fixtures.capability_gating import resolve_identity

    df = make_df({"x": [1]}, backend)
    assert matrix_identity(backend) == resolve_identity(df)


@pytest.fixture
def isolated_registry():
    from mountainash.core.capabilities.registry import CapabilityRegistry

    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield CapabilityRegistry
    finally:
        CapabilityRegistry.restore(snapshot)


def test_scalar_option_gate_uses_emitted_iana_timezone_value() -> None:
    from mountainash.core.capabilities.schema import ValueClass
    from expressions.argument_types._test_template import first_scalar_build_gate

    import mountainash as ma

    node = ma.col("ts").dt.local_timestamp("UTC").node
    fact = first_scalar_build_gate(node, matrix_identity("ibis"))
    assert fact is not None
    assert fact.param == "timezone"
    assert fact.value_class is ValueClass.IANA_TIMEZONE


def test_scalar_option_gate_ignores_non_gating_fact(isolated_registry) -> None:
    from mountainash.core.capabilities.schema import (
        Boundary,
        CapabilityFact,
        CapabilityLevel,
        Enforcement,
    )
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING,
    )
    from expressions.argument_types._test_template import first_scalar_build_gate

    import mountainash as ma

    node = ma.col("x").str.contains("a").node
    isolated_registry.register_backend(CONST_BACKEND.IBIS, [
        CapabilityFact(
            operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            param="case_sensitivity",
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message="router-only test fact",
            since="2026-08-09",
            boundary=Boundary.BUILD,
            enforcement=Enforcement.ROUTER_METADATA,
        ),
    ])
    assert first_scalar_build_gate(node, matrix_identity("ibis")) is None


def test_dynamic_argument_gate_precedes_wildcard_residue() -> None:
    from mountainash.core.capabilities.schema import CapabilityLevel
    from expressions.argument_types._test_template import first_scalar_build_gate

    import mountainash as ma

    node = ma.col("items").list.contains(ma.col("needle")).node
    fact = first_scalar_build_gate(node, matrix_identity("narwhals-pandas"))
    assert fact is not None
    assert fact.level is CapabilityLevel.LITERAL_ONLY


def test_param_gate_wins_over_wildcard_residue(isolated_registry) -> None:
    """A reachable parameter-specific GATE/BUILD fact must be selected even when
    a WILDCARD MATERIALIZE_RESIDUE fact is also registered for the same op —
    residue is a later, materialize-time fallback, never a shadow of a build gate."""
    from mountainash.core.capabilities.schema import (
        Boundary,
        CapabilityFact,
        CapabilityLevel,
        Enforcement,
        WILDCARD_PARAM,
    )
    from mountainash.core.types import BackendCapabilityError
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING,
    )
    from expressions.argument_types._test_template import first_scalar_build_gate

    import mountainash as ma

    node = ma.col("x").str.contains("a").node
    isolated_registry.register_backend(CONST_BACKEND.IBIS, [
        CapabilityFact(
            operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            param="case_sensitivity",
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message="param-specific build gate",
            since="2026-08-09",
            boundary=Boundary.BUILD,
            enforcement=Enforcement.GATE,
        ),
        CapabilityFact(
            operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS,
            param=WILDCARD_PARAM,
            level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            message="whole-op materialize residue",
            since="2026-08-09",
            boundary=Boundary.MATERIALIZE,
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            native_errors=(BackendCapabilityError,),
        ),
    ])
    fact = first_scalar_build_gate(node, matrix_identity("ibis"))
    assert fact is not None
    assert fact.param == "case_sensitivity"
    assert fact.enforcement is Enforcement.GATE
